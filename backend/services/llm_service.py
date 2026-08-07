"""LLM service with a provider abstraction.

The rest of the application only talks to :class:`LLMService`.  A provider
implements the small :class:`LLMProvider` protocol:

* ``OpenAICompatibleProvider`` — talks to any OpenAI-compatible
  ``/chat/completions`` endpoint (OpenAI, Azure, Groq, Together, and Google
  Gemini's OpenAI-compatible endpoint).  The base URL, model and key come
  exclusively from environment variables.
* ``MockProvider`` — deterministic offline responses for demos and tests
  when ``LLM_MOCK_MODE=true`` and no key is set.  It never requires a key.

Every completion is validated against a Pydantic schema; the provider
repairs malformed JSON once and retries before giving up.
"""
from __future__ import annotations

import asyncio
import json
import re
from abc import ABC, abstractmethod
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from config import Settings
from utils.context import current_session
from utils.errors import LLMError, LLMNotConfiguredError, LLMUnavailableError
from utils.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def _extract_json(text: str) -> str:
    """Extract the JSON object from a completion, tolerating fences/extra text."""
    match = _JSON_BLOCK_RE.search(text)
    if match:
        return match.group(1).strip()
    # Find the outermost {...} block.
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text.strip()


class LLMProvider(ABC):
    """Minimal provider interface. Implementations must be async."""

    @abstractmethod
    async def complete(
        self,
        *,
        model: str,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
        timeout: float,
    ) -> str:
        """Return the raw completion text for the given prompt pair."""
        raise NotImplementedError


class OpenAICompatibleProvider(LLMProvider):
    """Talks to any OpenAI-compatible ``/chat/completions`` endpoint."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(
            base_url=settings.llm_base_url.rstrip("/"),
            timeout=httpx.Timeout(settings.llm_timeout_seconds),
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def complete(
        self,
        *,
        model: str,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
        timeout: float,
    ) -> str:
        if not self._settings.llm_api_key:
            raise LLMNotConfiguredError(
                "LLM_API_KEY is not set. Add it to backend/.env "
                "(see .env.example) or enable LLM_MOCK_MODE for demos."
            )
        payload: dict[str, Any] = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if self._settings.llm_json_mode:
            payload["response_format"] = {"type": "json_object"}
        try:
            response = await self._client.post(
                "/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self._settings.llm_api_key}",
                    "Content-Type": "application/json",
                },
                timeout=timeout,
            )
        except httpx.HTTPError as exc:
            raise LLMError(f"LLM request failed: {exc}") from exc

        if response.status_code != 200:
            raise LLMError(
                f"LLM provider returned HTTP {response.status_code}: "
                f"{response.text[:500]}"
            )

        try:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise LLMError(f"Malformed LLM response: {exc}") from exc


class MockProvider(LLMProvider):
    """Deterministic offline provider for demos and tests.

    Produces plausible, topic-aware structured JSON without any network call.
    Only used when ``LLM_MOCK_MODE=true``; never in production.
    """

    async def complete(
        self,
        *,
        model: str,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
        timeout: float,
    ) -> str:
        combined = f"{system}\n{user}"
        topic = "this topic"
        topic_match = re.search(r"^- Topic: (.+)$", user, re.MULTILINE)
        if not topic_match:
            topic_match = re.search(r"TOPICS: (.+)", user)
        if topic_match:
            topic = topic_match.group(1).strip().splitlines()[0]

        if "Generate ONE interview question" in combined:
            return json.dumps(
                {
                    "question": f"Let's talk about {topic}. Explain the core idea "
                    "behind it and one real-world trade-off you'd need to manage.",
                    "topic": topic,
                    "intent": "Establish understanding of the topic.",
                    "question_type": "conceptual",
                }
            )
        if "Evaluate the candidate" in combined:
            return json.dumps(
                {
                    "score": 7,
                    "verdict": "good",
                    "follow_up": "next_topic",
                    "mastered_topic": True,
                    "notes": "Mock provider: reasonable, on-topic answer.",
                }
            )
        if "Follow-up strategy" in combined:
            return json.dumps(
                {
                    "question": f"Interesting — and could you explain how you'd "
                    f"approach '{topic}' if a team depended on it in production?",
                    "intent": "Probe depth on the current topic.",
                    "difficulty": "medium",
                }
            )
        if "The interview is finished" in combined:
            return json.dumps(
                {
                    "summary": "Solid overall performance with good coverage of "
                    "the core topics and room to deepen production experience.",
                    "strengths": [
                        "Clear explanations of core concepts",
                        "Good structured approach to design questions",
                    ],
                    "gaps": [
                        "Production deployment experience is limited",
                        "Some trade-off analysis was shallow",
                    ],
                    "next": [
                        "Practice system design for the topics covered",
                        "Review deployment and debugging scenarios",
                    ],
                    "score": 72,
                    "confidence": 0.7,
                    "topics_covered": [topic],
                }
            )
        raise LLMError("Mock provider received an unknown prompt type.")


class LLMService:
    """Facade over providers with Pydantic-validated structured completions."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._provider: LLMProvider
        if settings.llm_mock_mode:
            self._provider = MockProvider()
            logger.warning("LLM_MOCK_MODE=true — using the deterministic mock provider")
        else:
            self._provider = OpenAICompatibleProvider(settings)
        self._in_flight = 0

    async def close(self) -> None:
        if isinstance(self._provider, OpenAICompatibleProvider):
            await self._provider.close()

    @property
    def configured(self) -> bool:
        return self._settings.llm_configured

    @property
    def provider_name(self) -> str:
        return "mock" if self._settings.llm_mock_mode else self._settings.llm_provider

    async def structured_completion(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: type[T],
    ) -> T:
        """Ask the model for JSON and return a validated Pydantic instance."""
        if not self.configured:
            raise LLMNotConfiguredError(
                "No LLM provider is configured. Set LLM_API_KEY in "
                "backend/.env or enable LLM_MOCK_MODE=true for demos."
            )

        system = system_prompt + (
            "\n\nIMPORTANT: Reply with a single JSON object only, no "
            "markdown, no commentary."
        )

        session = current_session.get()
        primary_model = session.llm_model if session and session.llm_model else self._settings.llm_model
        
        candidates = [primary_model]
        for m in self._settings.llm_fallback_models:
            if m not in candidates:
                candidates.append(m)

        disallowed = {
            "meta-llama/llama-prompt-guard-2-22m",
            "meta-llama/llama-prompt-guard-2-86m",
            "openai/gpt-oss-safeguard-20b"
        }
        candidates = [m for m in candidates if m not in disallowed]

        last_error: Exception | None = None
        
        for model in candidates:
            attempts = 0
            prompt_to_send = user_prompt 
            
            while attempts < 4:
                attempts += 1
                try:
                    raw = await self._provider.complete(
                        model=model,
                        system=system,
                        user=prompt_to_send,
                        temperature=self._settings.llm_temperature,
                        max_tokens=self._settings.llm_max_tokens,
                        timeout=self._settings.llm_timeout_seconds,
                    )
                except LLMNotConfiguredError:
                    raise
                except LLMError as exc:
                    last_error = exc
                    exc_str = str(exc).lower()
                    is_retryable = any(kw in exc_str for kw in ["429", "capacity", "timeout", "rate limit", "503"])
                    if is_retryable and attempts < 4:
                        delay = [1, 2, 4][attempts - 1]
                        logger.warning("Retryable error on %s (attempt %d). Sleeping %ds: %s", model, attempts, delay, exc)
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error("Model %s failed (attempt %d): %s", model, attempts, exc)
                        break

                try:
                    payload = json.loads(_extract_json(raw))
                    result = schema.model_validate(payload)
                    
                    if session and session.llm_model != model:
                        logger.info("Session fallback: switching to %s (was %s)", model, session.llm_model)
                        session.llm_model = model
                        
                    return result
                except (json.JSONDecodeError, ValidationError) as exc:
                    last_error = exc
                    logger.warning("JSON validation failed on %s (attempt %d): %s", model, attempts, exc)
                    if attempts < 4:
                        prompt_to_send = (
                            f"Your previous reply was not valid JSON matching the "
                            f"required schema. Fix it. Required fields:\n"
                            f"{schema.model_json_schema()}\n\nOriginal request:\n"
                            f"{user_prompt}"
                        )
                        continue
                    else:
                        break

            if model != candidates[-1]:
                logger.info("Fallback triggered: moving from %s to next model.", model)

        logger.error("All LLM fallback models failed. Last error: %s", last_error)
        raise LLMUnavailableError("The AI service is temporarily unavailable. Please try again in a moment.")
