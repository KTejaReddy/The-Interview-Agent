"""Test the follow-up generation path.

Uses a fake LLM provider that returns scripted evaluation/follow-up results
so the ``_ask_follow_up`` branch in the interview manager is exercised.
"""
from __future__ import annotations

import json

import pytest
from pydantic import BaseModel

from agents.candidate_analyzer import CandidateAnalyzer
from agents.difficulty_manager import DifficultyManager
from agents.feedback_generator import FeedbackGenerator
from agents.followup_generator import FollowUpGenerator
from agents.interview_manager import InterviewManager
from agents.question_planner import QuestionPlanner
from agents.response_evaluator import ResponseEvaluator
from config import Settings
from memory.context_manager import ContextManager
from retrieval.candidate_loader import CandidateLoader
from retrieval.curriculum_loader import CurriculumLoader
from retrieval.curriculum_retriever import CurriculumRetriever
from schemas.llm import EvaluationDraft, FollowUpDraft, FeedbackDraft, QuestionDraft
from services.llm_service import LLMProvider
from services.prompt_builder import PromptBuilder
from services.session_manager import SessionManager
from tests.conftest import FIXTURES_DIR


class _ScriptedProvider(LLMProvider):
    """LLM provider with scripted return values for each schema type."""

    def __init__(self) -> None:
        self.evaluation_call = 0

    async def complete(
        self,
        *,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
        timeout: float,
    ) -> str:
        combined = f"{system}\n{user}"

        if "Generate ONE interview question" in combined:
            return json.dumps({
                "question": "Explain the core concepts and trade-offs involved.",
                "topic": "test-topic",
                "intent": "Probe understanding.",
                "question_type": "conceptual",
            })

        if "Evaluate the candidate" in combined:
            self.evaluation_call += 1
            if self.evaluation_call == 1:
                return json.dumps({
                    "score": 8,
                    "verdict": "good",
                    "follow_up": "deeper",
                    "mastered_topic": False,
                    "notes": "Solid answer, probe deeper.",
                })
            return json.dumps({
                "score": 7,
                "verdict": "good",
                "follow_up": "next_topic",
                "mastered_topic": True,
                "notes": "Good enough, move on.",
            })

        if "Follow-up strategy" in combined:
            return json.dumps({
                "question": "Interesting — can you elaborate on the production edge case?",
                "intent": "Probe depth.",
                "difficulty": "advanced",
            })

        if "The interview is finished" in combined:
            return json.dumps({
                "summary": "Solid overall.",
                "strengths": ["Clear answers"],
                "gaps": ["Deeper dive needed"],
                "next": ["Practice more"],
                "score": 75,
                "confidence": 0.7,
                "topics_covered": ["test-topic"],
            })

        raise ValueError(f"Unknown prompt type: {combined[:80]}")


class FakeLLM:
    """Minimal LLM service stand-in."""

    def __init__(self) -> None:
        self._provider = _ScriptedProvider()

    async def structured_completion(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: type[BaseModel],
    ) -> BaseModel:
        raw = await self._provider.complete(
            system=system_prompt,
            user=user_prompt,
            temperature=0.0,
            max_tokens=200,
            timeout=10,
        )
        payload = json.loads(raw)
        return schema.model_validate(payload)

    @property
    def configured(self) -> bool:
        return True


@pytest.mark.asyncio
async def test_follow_up_branch() -> None:
    settings = Settings()
    sessions = SessionManager(settings)
    candidates = CandidateLoader(FIXTURES_DIR)
    candidates.load()
    curriculum = CurriculumLoader(FIXTURES_DIR)
    curriculum.load()
    retriever = CurriculumRetriever(curriculum)
    prompts = PromptBuilder(settings)
    fake = FakeLLM()
    difficulty = DifficultyManager()

    planner = QuestionPlanner(
        fake, prompts, retriever, difficulty_manager=difficulty,
    )
    evaluator = ResponseEvaluator(fake, prompts)
    followups = FollowUpGenerator(fake, prompts, retriever, difficulty_manager=difficulty)
    feedback_gen = FeedbackGenerator(fake, prompts)
    manager = InterviewManager(
        settings, sessions, fake, prompts, retriever,
        candidates, CandidateAnalyzer(), planner, evaluator,
        followups, feedback_gen, ContextManager(),
    )

    LONG_INTRO = "Hi! I'm Alex Doe, a junior Python developer working on REST APIs."

    # Create the session (the message is stored but not duplicated).
    session = await manager.start_session("CAND-001", LONG_INTRO)

    # Turn 1: send the same long message → intro is skipped → Q1 is asked.
    r0 = await manager.handle_message(session, LONG_INTRO)
    assert r0.state == "QUESTIONING", f"Expected QUESTIONING (intro skipped), got {r0.state}"
    assert r0.question_number == 1

    # Turn 2: answer Q1 → evaluator returns "deeper" → FOLLOW_UP.
    r1 = await manager.handle_message(
        session, "Classes are blueprints for objects, and I keep them single-responsibility."
    )
    assert r1.state == "FOLLOW_UP", f"Expected FOLLOW_UP, got {r1.state}"
    assert session.follow_ups_used == 1
    assert "elaborate" in r1.message

    # Turn 3: answer the follow-up → evaluator returns "next_topic" → Q2.
    r2 = await manager.handle_message(session, "I'd verify invariants and write unit tests.")
    assert r2.state == "QUESTIONING"
    assert r2.question_number == 2

    # Verify conversation memory.
    # Turn 0: answer to the base question (not a follow-up).
    # Turn 1: answer to the follow-up (is_follow_up=True).
    assert session.memory.count == 2
    base_turn = session.memory.all_turns[0]
    assert base_turn.is_follow_up is False
    assert base_turn.verdict.value == "good"
    follow_up_turn = session.memory.all_turns[1]
    assert follow_up_turn.is_follow_up is True
    assert follow_up_turn.score == 7  # second evaluation call returns score 7

    assert await sessions.size() == 1