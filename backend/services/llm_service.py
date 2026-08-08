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

#: Words that never make a mention relevant to a question concept.
_STOPWORDISH = {
    "the", "and", "with", "for", "you", "your", "that", "this", "what",
    "how", "when", "where", "why", "from", "into", "about", "using",
    "build", "create", "learn", "understand", "explain", "setup", "work",
}


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
        topic = self._topic_from(user)

        if "Generate ONE interview question" in combined:
            return json.dumps(self._mock_question(user, topic))
        if "Evaluate the candidate" in combined:
            return json.dumps(self._mock_evaluation(user, topic))
        if "Follow-up strategy" in combined:
            return json.dumps(self._mock_follow_up(user, topic))
        if "The interview is finished" in combined:
            return json.dumps(self._mock_feedback(user))
        raise LLMError("Mock provider received an unknown prompt type.")

    @staticmethod
    def _field(user: str, pattern: str) -> str:
        match = re.search(pattern, user, re.MULTILINE)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _topic_from(user: str) -> str:
        topic_match = re.search(r"^- Topic: (.+)$", user, re.MULTILINE)
        if not topic_match:
            topic_match = re.search(r"TOPICS: (.+)", user)
        if topic_match:
            return topic_match.group(1).strip().splitlines()[0]
        return "this topic"

    def _concept_from(self, user: str) -> str:
        """Technical concept derived from the curriculum objective (the mock
        questions ask about the concept, never the day title)."""
        concept = self._field(user, r"^- Technical concept: (.+)$")
        if not concept:
            concept = self._field(user, r"^- Topic: (.+)$")
        return concept or "this concept"

    def _objective_from(self, user: str) -> str:
        return self._field(user, r"^- Learning objective: (.+)$")

    #: Recognizable misconception phrases.  A negation inside the 10 chars
    #: before the marker ("I wouldn't use LIKE...", "rather than...") means
    #: the candidate is *criticising* the misconception, not holding it.
    _MISCONCEPTION_MARKERS = (
        re.compile(r"(?:store[sd]?|storing)\s+the\s+original\s+text", re.I),
        re.compile(r"store[sd]?\s+the\s+text\s+itself", re.I),
        re.compile(r"\b(?:just\s+)?(?:use|using)\s+(?:a\s+)?sql\s+like\b", re.I),
        re.compile(r"\blike\s+query\s+(?:on|against)\s+the\s+raw\s+text", re.I),
        re.compile(r"\bthe\s+model\s+remembers\s+everything\b", re.I),
        re.compile(r"\bembeddings?\s+(?:are|is)\s+the\s+(?:words|documents?)\s+themselves", re.I),
        re.compile(r"\bno\s+(?:need\s+for\s+a\s+)?vector\s+database\s+needed\b", re.I),
        re.compile(r"\bsearch\s+is\s+just\s+keyword\s+(?:search|matching)\b", re.I),
    )
    _NEGATION_HINT = re.compile(
        r"\b(?:not|no|never|avoid|without|wouldn'?t|don'?t|shouldn'?t|couldn'?t|rather than|instead of|unlike)\b",
        re.I,
    )

    @classmethod
    def _detects_misconception(cls, answer: str) -> bool:
        """True when the answer asserts one of a small set of recognizable
        technical misconceptions (deterministic stand-in for the real LLM's
        correctness judgement in mock mode)."""
        if not answer:
            return False
        for pattern in cls._MISCONCEPTION_MARKERS:
            for match in pattern.finditer(answer):
                window = answer[max(0, match.start() - 10): match.start()]
                if not cls._NEGATION_HINT.search(window):
                    return True
        return False

    @staticmethod
    def _field_block(user: str, start: str, end: str) -> str:
        """Text between two section markers (each matched at line start)."""
        pattern = re.compile(
            re.escape(start) + r"\s*\n(.*?)\n\s*" + re.escape(end),
            re.DOTALL,
        )
        match = pattern.search(user)
        return match.group(1).strip() if match else ""

    def _mock_feedback(self, user: str) -> dict[str, Any]:
        """Evidence-based mock feedback: derived from the actual transcript
        and per-topic assessment state in the prompt, never a canned
        paragraph.  Strengths come from topics with demonstrated good
        scores, gaps from topics with repeated failures / low confidence,
        and the score from the actual answer scores."""
        assessment_block = self._field_block(
            user,
            "ASSESSMENT STATE (per-topic, derived from the actual interview)",
            "PROFILE TOPICS NOT TESTED",
        )
        topics: list[tuple[str, str, int, int, int]] = []
        for line in assessment_block.splitlines():
            # knowledge_status is the authoritative per-topic verdict.
            match = re.match(
                r"^- (.+?): knowledge_status=(\w+), confidence=(\w+), "
                r"failures=(\d+), bare_claims=(\d+), "
                r"score range (\d+)-(\d+)/10",
                line.strip(),
            )
            if match:
                topics.append(
                    (
                        match.group(1),
                        match.group(2),  # knowledge_status
                        int(match.group(4)),  # failures
                        int(match.group(6)),  # worst
                        int(match.group(7)),  # best
                    )
                )

        transcript = self._field_block(user, "FULL INTERVIEW TRANSCRIPT", "CANDIDATE PROFILE")
        scores = re.findall(r"score=(\d+)/10 verdict=(\w+)", transcript)
        avg = sum(int(s) for s, _ in scores) / max(1, len(scores)) if scores else 0.0

        # Defensive: if the assessment block could not be parsed, recover
        # the covered topics straight from the transcript's own topic lines
        # (the feedback must never report 0 topics when topics were asked).
        if not topics:
            topic_lines = re.findall(r"^\[Q\d+.*?\] (.+)$", transcript, re.MULTILINE)
            topics = [
                (topic, "unknown", 0, 0, 0)
                for topic in dict.fromkeys(topic_lines)
            ]

        strong_topics = [
            t for t, status, _f, _w, b in topics
            if status == "demonstrated" or (status == "partially_demonstrated" and b >= 7)
        ]
        weak_topics = [
            t for t, status, f, _w, b in topics
            if status in ("insufficient_evidence", "incorrect", "unknown")
            or f >= 2 or b <= 4
        ]
        covered = len(topics)

        if strong_topics:
            strengths = [
                f"Showed a working understanding of {t} when explaining it during the interview"
                for t in strong_topics
            ]
        else:
            # No demonstrated strengths.  The feedback schema requires at
            # least one strength, so give a truthful, non-knowledge item —
            # never a false competence claim nor a misleading "Engaged with
            # every question" when the answers were "I don't know".
            partials = [
                t for t, status, _f, _w, _b in topics
                if status == "partially_demonstrated"
            ]
            strengths = (
                [f"Showed partial understanding of {partials[0]} — room to go deeper"]
                if partials
                else ["Responded consistently to every question asked during the interview"]
            )
        gaps = [
            f"Did not demonstrate sufficient understanding of {t} during the interview"
            for t in weak_topics
        ] or ["No significant technical gaps surfaced during the interview"]
        next_steps = [
            f"Review the curriculum material and exercises for {t}"
            for t in (weak_topics[:2] or strong_topics[:1] or ["the topics covered"])
        ]
        score = int(
            round(min(100.0, max(0.0, avg * 8.0 + min(20.0, covered * 2.5))))
        )
        summary = (
            f"The interview covered {covered} curriculum topics with an average "
            f"answer score of {avg:.1f}/10."
            + (
                f" Strongest areas: {', '.join(strong_topics[:3])}."
                if strong_topics
                else " Most answers did not demonstrate the underlying concepts."
            )
        )
        return {
            "summary": summary,
            "strengths": strengths[:4],
            "gaps": gaps[:4],
            "next": next_steps[:4],
            "score": score,
            "confidence": round(max(0.0, min(1.0, avg / 10.0)), 2),
            "topics_covered": [t for t, _c, _f, _w, _b in topics],
        }

    @staticmethod
    def _answer_from(user: str) -> str:
        match = re.search(
            r"CANDIDATE'S ANSWER\n(.*?)\n\n(?:CANDIDATE PROFILE|EVALUATION)",
            user,
            re.DOTALL,
        )
        return match.group(1).strip() if match else ""

    def _mock_question(self, user: str, topic: str) -> dict[str, Any]:
        """Concept-grounded question text for each cognitive task.  The
        concept comes from the curriculum's own learning objective, so the
        mock never produces \"What is <Day title>?\" questions.  Questions
        stay short and conversational (one idea, no multi-part phrasing).
        Roughly one in four questions may open with a natural reference to a
        curriculum concept the candidate raised earlier (context retention)
        — never on every question, and only when the candidate actually
        mentioned it."""
        from utils.concepts import action_phrase_from_objective

        concept = self._concept_from(user)
        objective = self._objective_from(user)
        action = action_phrase_from_objective(objective) if objective else concept
        type_match = re.search(r"- Question type: (\w+)", user)
        qtype = type_match.group(1) if type_match else "conceptual"
        position = re.search(r"question (\d+) of", user)
        n = int(position.group(1)) if position else 0

        # Context retention: occasionally build on a concept the candidate
        # raised earlier, in their own words — but at most ~1 in 4 questions
        # (so it never becomes a repetitive "You mentioned X earlier" opener)
        # AND only when the mention is actually relevant to THIS question's
        # concept (a human only references what connects to the topic).
        mention_prefix = ""
        mention_match = re.search(r"- Candidate mentioned earlier: (.+)$", user, re.MULTILINE)
        if mention_match and n % 4 == 1:
            mentions = [
                m.strip()
                for m in mention_match.group(1).split(",")
                if m.strip() and m.strip() != "none yet"
            ]
            if mentions:
                # Relevance gate: the mention must share a meaningful token
                # with the question's concept/objective, or the prefix would
                # be a non-sequitur ("You mentioned Docker" -> embeddings).
                relevance_haystack = f"{concept} {objective}".lower()
                chosen = None
                for mention in mentions:
                    tokens = [
                        w for w in mention.lower().split()
                        if len(w) >= 4 and w not in _STOPWORDISH
                    ]
                    if any(token in relevance_haystack for token in tokens):
                        chosen = mention
                        break
                if chosen:
                    mention_prefix = f"You mentioned {chosen} earlier — "

        # Rotate phrasings so consecutive questions on the same day still
        # read differently.
        conceptual_variants = (
            f"Can you explain {concept} — and why it matters?",
            f"Walk me through {concept}.",
            f"How would you explain {concept} to a teammate who just joined?",
        )
        templates = {
            "definition": f"In your own words, can you walk me through {concept}?",
            "conceptual": conceptual_variants[n % len(conceptual_variants)],
            "scenario": (
                f"Let's make it concrete: the team is tasked with {action}. "
                f"How would you approach it?"
            ),
            "architecture": (
                f"Where does the responsibility for {action} sit in the "
                f"architecture, and why?"
            ),
            "debugging": (
                f"A teammate reports issues with {action} in production. "
                f"What's your first diagnostic step?"
            ),
            "tradeoffs": (
                f"What are the main trade-offs involved in {action} in a real "
                f"system?"
            ),
            "design": (
                f"If you had to build a small feature around {action}, what "
                f"would you sketch first?"
            ),
            "production": (
                f"If your team relied on {action} in production, what would "
                f"you monitor?"
            ),
            "deployment": (
                f"How would you ship a change involving {action} and roll it "
                f"back safely?"
            ),
            "reasoning": (
                f"When is {action} worth the effort, and when would you avoid "
                f"it?"
            ),
        }
        question = templates.get(qtype, templates["conceptual"])

        return {
            "question": f"{mention_prefix}{question}",
            "topic": topic,
            "intent": f"Assess the learning objective behind '{concept}'.",
            "question_type": qtype,
        }

    def _mock_follow_up(self, user: str, topic: str) -> dict[str, Any]:
        """Strategy-aware, evidence-grounded follow-ups.  Deep follow-ups
        ESCALATE the cognitive level as follow-up count grows (application →
        trade-off → architecture/production) instead of cycling a fixed set,
        so strong candidates get a ladder, never a main→example→mistake
        bundle.  Activity-style templates use the gerund action phrase and
        explanation-style ones the "how …" concept — so a template can never
        produce "How does how to build X fit…?".  The "what's the core job
        of X" template is banned: simplifications are concept-grounded and
        rotated so they never read as a script."""
        from utils.concepts import action_phrase_from_objective

        strategy_match = re.search(r"- Follow-up strategy: (\w+)", user)
        strategy = strategy_match.group(1) if strategy_match else "deeper"
        concept = self._concept_from(user)
        objective = self._objective_from(user)
        action = (
            action_phrase_from_objective(objective)
            if objective
            else concept
        )
        answer = self._answer_from(user)
        snippet = " ".join(answer.split()[:8])
        # Follow-ups so far on this topic drive the cognitive escalation.
        count_match = re.search(r"- Follow-ups so far on this topic: (\d+)", user)
        count = int(count_match.group(1)) if count_match else 0

        # Rotation seed derived from the concept itself, so consecutive
        # topics open with DIFFERENT phrasings (the per-topic count is 0 for
        # every first follow-up, which is why the old opener repeated).
        seed = sum(ord(ch) for ch in concept) if concept else count

        # Short, rotating acknowledgements so the same stock phrase is never
        # repeated ("Glad to hear it…", "No problem — let's ground this
        # differently…", "Let's try a simpler angle…" on every turn are
        # banned).
        openers = {
            "deeper": (
                "Good — let's go one level deeper. ",
                "Right. Let's push on that. ",
                "Exactly. Next angle: ",
            ),
            "simplify": (
                "Okay, let's make that easier. ",
                "Let's try this from a different direction. ",
                "No worries, let's start simpler. ",
                "Let's break it down a bit. ",
            ),
            "recovery": (
                "Let's step back for a second. ",
                "Let's approach it differently. ",
            ),
            "verify": (
                "Alright, let's test that. ",
                "Good — let's see it in action. ",
                "Okay, let's make it concrete. ",
            ),
            "probe": ("", ""),
        }
        pool = openers.get(strategy, openers["deeper"])
        opener = pool[(seed + count) % len(pool)]

        # Escalating ladder for strong answers (never repeats an angle).
        deeper_ladder = (
            f"Suppose {action} had to be production-ready next month — what's "
            f"the first thing you'd verify?",
            f"What trade-off would you weigh between {action} and a simpler "
            f"alternative in a real system?",
            f"Where does {action} sit in the architecture, and what would you "
            f"monitor in production?",
        )

        # Concept-grounded simplifications — never "what's the core job of X".
        simplify_variants = (
            f"What would {action} look like in practice?",
            f"Let's break it down: what does {action} actually involve?",
            f"Can you walk me through {action} from the very first step?",
            f"What's the simplest way to think about {action}?",
        )

        templates = {
            "deeper": opener + deeper_ladder[min(count, len(deeper_ladder) - 1)],
            "simplify": opener + simplify_variants[(seed + count) % len(simplify_variants)],
            "recovery": opener + f"How would you explain {concept} to a junior teammate?",
            "verify": opener + f"Walk me through {concept} with a concrete example.",
            "probe": f"You said \"{snippet}\" — could you expand on that?",
        }
        return {
            "question": templates.get(strategy, templates["deeper"]),
            "intent": (
                f"Follow up ({strategy}) on '{concept}' — "
                f"follow-up #{count + 1} on this topic."
            ),
            "difficulty": (
                "easy"
                if strategy in ("simplify", "recovery")
                else "medium"
            ),
        }

    def _mock_evaluation(self, user: str, topic: str) -> dict[str, Any]:
        """Answer-aware evaluation: IDK and bare knowledge claims are never
        treated as competence; recognizable misconceptions are marked wrong;
        otherwise longer, substantive answers score higher.  This keeps the
        mock deterministic while exercising the same adaptive behaviour as
        the real evaluator."""
        from utils.answer_signals import (
            detects_claim_without_evidence,
            detects_greeting,
            detects_idk,
        )

        answer = self._answer_from(user)

        if detects_idk(answer):
            return {
                "score": 2,
                "verdict": "weak",
                "follow_up": "simplify",
                "mastered_topic": False,
                "notes": "No substantive answer given.",
            }
        if detects_greeting(answer):
            return {
                "score": 2,
                "verdict": "weak",
                "follow_up": "simplify",
                "mastered_topic": False,
                "notes": "Greeting/non-answer given.",
            }
        if detects_claim_without_evidence(answer):
            return {
                "score": 4,
                "verdict": "unclear",
                "follow_up": "verify",
                "mastered_topic": False,
                "notes": "Asserted knowledge without demonstrating it.",
            }
        if self._detects_misconception(answer):
            return {
                "score": 2,
                "verdict": "wrong",
                "follow_up": "recovery",
                "mastered_topic": False,
                "notes": "The answer contains a recognizable misconception — probe it.",
            }

        length = len(answer)
        if length >= 240:
            return {
                "score": 9,
                "verdict": "excellent",
                "follow_up": "deeper",
                "mastered_topic": True,
                "notes": "Detailed, well-structured answer.",
            }
        if length >= 120:
            return {
                "score": 8,
                "verdict": "good",
                "follow_up": "deeper" if "trade" in answer.lower() else "next_topic",
                "mastered_topic": True,
                "notes": "Solid, on-topic answer.",
            }
        if length >= 60:
            return {
                "score": 6,
                "verdict": "good",
                "follow_up": "probe",
                "mastered_topic": False,
                "notes": "Correct but shallow — probe for depth.",
            }
        return {
            "score": 3,
            "verdict": "weak",
            "follow_up": "simplify",
            "mastered_topic": False,
            "notes": "Short or non-committal answer.",
        }


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
