"""Interview-intelligence regression tests.

Covers the fixes that make the interviewer assess *concepts*, not course
titles:

* concept derivation from learning objectives (never the day title),
* "I know" / "yes" is NOT competence — it triggers a verify probe,
* "I don't know" ladder: one simpler diagnostic -> move on,
* planner questions are grounded in a real learning objective,
* learning objectives rotate within a day (no repeated assessments),
* the mock provider never produces "What is <Day title>?" questions.
"""
from __future__ import annotations

import pytest

from agents.candidate_analyzer import CandidateAnalyzer
from agents.followup_generator import _fallback_question
from agents.question_planner import QuestionPlanner
from agents.response_evaluator import ResponseEvaluator
from config import settings
from memory.context_manager import ContextManager, InterviewContext
from memory.conversation_memory import ConversationMemory
from models.candidate_profile import CandidateProfile
from models.enums import Difficulty, FollowUpStrategy, QuestionType, Verdict
from models.interview_state import InterviewState
from models.plan import InterviewPlan, PlannedQuestion
from retrieval.candidate_loader import CandidateLoader
from retrieval.curriculum_loader import CurriculumLoader
from retrieval.curriculum_retriever import CurriculumRetriever
from services.llm_service import LLMService
from services.prompt_builder import PromptBuilder
from tests.conftest import FIXTURES_DIR
from utils.answer_signals import (
    detects_claim_without_evidence,
    detects_idk,
)
from utils.concepts import action_phrase_from_objective, concept_from_objective


# ---------------------------------------------------------------------------
# follow-up fallback phrase safety
# ---------------------------------------------------------------------------


def _objective_question() -> PlannedQuestion:
    return _question(
        learning_objective="Create a /chat API endpoint for the healthcare chatbot",
        concept="how to create a /chat API endpoint for the healthcare chatbot",
    )


def test_fallback_question_never_glues_phrase_forms() -> None:
    """Fallback follow-ups must never produce malformed sentences like
    "How does how to build X fit…?" regardless of the strategy."""
    question = _objective_question()
    for strategy in (
        FollowUpStrategy.DEEPER,
        FollowUpStrategy.SIMPLIFY,
        FollowUpStrategy.RECOVERY,
        FollowUpStrategy.VERIFY,
        FollowUpStrategy.PROBE,
    ):
        for count in range(3):
            text = _fallback_question(question, strategy, count)
            assert len(text) > 10
            assert "how does how to" not in text.lower()
            assert "how to how to" not in text.lower()
            assert "does how to" not in text.lower()
            assert "how does create" not in text.lower()
            assert "core job of how to" not in text.lower()
            # The curriculum objective is grounded in, never dropped.
            assert "chat API endpoint" in text or "chat api endpoint" in text.lower()


def test_fallback_question_rotates_angles() -> None:
    """Consecutive fallback follow-ups on the same topic differ (no fixed
    main -> example -> mistake bundle)."""
    question = _objective_question()
    seen = {
        _fallback_question(question, FollowUpStrategy.DEEPER, count)
        for count in range(3)
    }
    assert len(seen) == 3


def test_fallback_simplify_never_uses_core_job() -> None:
    """The universal \"what's the core job of X?\" simplification is banned:
    every simplify fallback is a concept-grounded question about the actual
    activity, so it can never read \"the core job of Secure chatbot APIs…\"."""
    question = _question(
        learning_objective="Secure chatbot APIs against unauthorized access",
        concept="how to secure chatbot APIs against unauthorized access",
    )
    for count in range(3):
        text = _fallback_question(question, FollowUpStrategy.SIMPLIFY, count)
        assert "core job" not in text.lower()
        assert "simpler angle" not in text.lower()
        assert "in one sentence" not in text.lower()
        assert len(text) > 10


# ---------------------------------------------------------------------------
# planner: deepen after coverage (no day-hopping once 4 days are met)
# ---------------------------------------------------------------------------


def test_planner_limits_revisits_to_two_mains_per_day() -> None:
    """A day may host a second (deeper) main question, but once it has two
    mains it is not selected again — the interview stays in the 4-6 day /
    8-10 question band instead of hopping to a new day every question."""
    retriever = _retriever()
    planner = QuestionPlanner(None, None, retriever)  # type: ignore[arg-type]
    profile = _profile("CAND-002")

    plan = InterviewPlan()
    plan.days_covered = [0, 1, 2, 3]
    for index in range(4):
        day = retriever.get_day(index)
        plan.questions.append(
            PlannedQuestion(
                day_index=index,
                day_title=day.title,
                topic=day.primary_topic,
                question_type=QuestionType.CONCEPTUAL,
                difficulty=Difficulty.MEDIUM,
                question="dummy",
            )
        )
    # Day 4 (index 3) already has 2 mains -> must not be picked a third time.
    plan.questions.append(
        PlannedQuestion(
            day_index=3,
            day_title=retriever.get_day(3).title,
            topic=retriever.get_day(3).primary_topic,
            question_type=QuestionType.CONCEPTUAL,
            difficulty=Difficulty.MEDIUM,
            question="dummy",
        )
    )

    day_index, _topic = planner._determine_next_topic(profile, plan)
    assert day_index != 3


def test_planner_deepens_after_coverage() -> None:
    """Once the 4-day minimum is met, the planner stays on the current day
    (depth) instead of hopping to every new day (breadth)."""
    retriever = _retriever()
    planner = QuestionPlanner(None, None, retriever)  # type: ignore[arg-type]
    profile = _profile("CAND-002")  # senior, all days completed

    plan = InterviewPlan()
    plan.days_covered = [0, 1, 2, 3]
    for index in range(4):
        day = retriever.get_day(index)
        plan.questions.append(
            PlannedQuestion(
                day_index=index,
                day_title=day.title,
                topic=day.primary_topic,
                question_type=QuestionType.CONCEPTUAL,
                difficulty=Difficulty.MEDIUM,
                question="dummy",
            )
        )
    day_index, _topic = planner._determine_next_topic(profile, plan)
    # The current day (last asked) is chosen again for depth.
    assert day_index == plan.questions[-1].day_index
    assert day_index == 3


def test_planner_prefers_uncovered_day_before_minimum() -> None:
    """Before the 4-day minimum is met, an uncovered day is prioritised."""
    retriever = _retriever()
    planner = QuestionPlanner(None, None, retriever)  # type: ignore[arg-type]
    profile = _profile("CAND-002")

    plan = InterviewPlan()
    plan.days_covered = [0, 1]
    for index in range(2):
        day = retriever.get_day(index)
        plan.questions.append(
            PlannedQuestion(
                day_index=index,
                day_title=day.title,
                topic=day.primary_topic,
                question_type=QuestionType.CONCEPTUAL,
                difficulty=Difficulty.MEDIUM,
                question="dummy",
            )
        )
    day_index, _topic = planner._determine_next_topic(profile, plan)
    assert day_index not in {0, 1}

# ---------------------------------------------------------------------------
# concept derivation
# ---------------------------------------------------------------------------


def test_concept_from_objective_cognitive_verb() -> None:
    assert (
        concept_from_objective(
            "Understand how text is converted into vector embeddings"
        )
        == "how text is converted into vector embeddings"
    )


def test_concept_from_objective_imperative() -> None:
    assert (
        concept_from_objective("Create a /chat API endpoint for the healthcare chatbot")
        == "how to create a /chat API endpoint for the healthcare chatbot"
    )


def test_action_phrase_gerund_chain() -> None:
    assert (
        action_phrase_from_objective(
            "Run and debug your first Python program inside VS Code"
        )
        == "running and debugging your first Python program inside VS Code"
    )


# ---------------------------------------------------------------------------
# answer signals
# ---------------------------------------------------------------------------


def test_idk_detection() -> None:
    assert detects_idk("I don't know")
    assert detects_idk("not sure")
    assert not detects_idk("I know embeddings map text to vectors by meaning")


def test_claim_without_evidence_detection() -> None:
    assert detects_claim_without_evidence("I know")
    assert detects_claim_without_evidence("Yes, I know that.")
    assert detects_claim_without_evidence("yeah")
    assert detects_claim_without_evidence("I understand")
    # A claim followed by real content is evidence, not a bare claim.
    assert not detects_claim_without_evidence(
        "Yes, embeddings convert text into vectors based on semantic "
        "similarity, which lets us compare meaning."
    )
    assert not detects_claim_without_evidence("I do not know")


# ---------------------------------------------------------------------------
# evaluator: "I know" and "I don't know"
# ---------------------------------------------------------------------------


def _context(
    plan: InterviewPlan | None = None,
    profile: CandidateProfile | None = None,
) -> InterviewContext:
    manager = ContextManager()
    return manager.build(
        state=InterviewState.QUESTIONING,
        candidate=profile
        or CandidateProfile(candidate_id="C", name="Test", role="Engineer"),
        plan=plan or InterviewPlan(),
        memory=ConversationMemory(),
        question_index=0,
    )


def _question(**overrides) -> PlannedQuestion:
    defaults = dict(
        day_index=0,
        day_title="Day 7 — Embeddings Explained",
        topic="Embeddings Explained",
        question_type=QuestionType.CONCEPTUAL,
        difficulty=Difficulty.MEDIUM,
        question="Can you explain how text is converted into vector embeddings?",
        intent="establish whether the candidate can explain the concept",
        learning_objective="Understand how text is converted into vector embeddings",
        concept="how text is converted into vector embeddings",
    )
    defaults.update(overrides)
    return PlannedQuestion(**defaults)


@pytest.mark.asyncio
async def test_iknow_triggers_verify_probe() -> None:
    """A bare knowledge claim must NOT be scored as competence."""
    llm = LLMService(settings)
    prompts = PromptBuilder(settings)
    evaluator = ResponseEvaluator(llm, prompts)
    plan = InterviewPlan()

    result = await evaluator.evaluate(
        _context(plan), _question(), "I know"
    )
    assert result.verdict == Verdict.UNCLEAR
    assert result.strategy == FollowUpStrategy.VERIFY
    assert result.score <= 5
    assert not result.mastered_topic
    assert result.wants_follow_up is True
    # A bare claim is not a demonstrated failure either.
    assessment = plan.assessment.get_topic("Embeddings Explained")
    assert assessment.consecutive_failures == 0
    assert assessment.confidence == "unknown"


@pytest.mark.asyncio
async def test_strong_answer_to_verify_probe_is_rewarded() -> None:
    llm = LLMService(settings)
    prompts = PromptBuilder(settings)
    evaluator = ResponseEvaluator(llm, prompts)
    plan = InterviewPlan()

    result = await evaluator.evaluate(
        _context(plan), _question(), "I know"
    )
    assert result.strategy == FollowUpStrategy.VERIFY

    strong = (
        "Text gets converted into embeddings by feeding each chunk through a "
        "sentence-transformer model that maps meaning into a high-dimensional "
        "vector space, so similar sentences land close together. You can then "
        "measure semantic similarity with cosine distance and store the "
        "vectors next to the original chunks for retrieval."
    )
    result2 = await evaluator.evaluate(_context(plan), _question(), strong)
    assert result2.verdict == Verdict.EXCELLENT
    assert plan.assessment.get_topic("Embeddings Explained").confidence == "high"


@pytest.mark.asyncio
async def test_idk_ladder_simplify_then_move_on() -> None:
    """A real interviewer gives a weak concept at most two attempts: one
    simpler diagnostic, then it moves on (never 5-6 questions on one
    concept the candidate cannot answer)."""
    llm = LLMService(settings)
    prompts = PromptBuilder(settings)
    evaluator = ResponseEvaluator(llm, prompts)
    plan = InterviewPlan()

    r1 = await evaluator.evaluate(_context(plan), _question(), "I don't know")
    assert r1.strategy == FollowUpStrategy.SIMPLIFY
    assert plan.assessment.get_topic("Embeddings Explained").consecutive_failures == 1

    r2 = await evaluator.evaluate(_context(plan), _question(), "I don't know")
    assert r2.strategy == FollowUpStrategy.NEXT_TOPIC
    assessment = plan.assessment.get_topic("Embeddings Explained")
    assert assessment.consecutive_failures == 2
    assert assessment.confidence == "low"


@pytest.mark.asyncio
async def test_greeting_is_non_substantive() -> None:
    """A greeting ("hello") is a non-answer: one short simpler recovery,
    never a long explanation about why the candidate didn't answer."""
    llm = LLMService(settings)
    prompts = PromptBuilder(settings)
    evaluator = ResponseEvaluator(llm, prompts)
    plan = InterviewPlan()

    result = await evaluator.evaluate(_context(plan), _question(), "hello")
    assert result.verdict == Verdict.WEAK
    assert result.strategy == FollowUpStrategy.SIMPLIFY
    assert result.score <= 3
    assert not result.mastered_topic
    # "hello" is a failure-to-answer, not a knowledge claim.
    assessment = plan.assessment.get_topic("Embeddings Explained")
    assert assessment.bare_claims == 0
    assert assessment.consecutive_failures == 1


@pytest.mark.asyncio
async def test_yes_is_a_non_answer_not_a_claim() -> None:
    """A bare "yes"/"yeah"/"sure" is filler, not a knowledge claim: it gets
    a simpler recovery (SIMPLIFY), while "I know" still triggers VERIFY."""
    llm = LLMService(settings)
    prompts = PromptBuilder(settings)
    evaluator = ResponseEvaluator(llm, prompts)

    plan1 = InterviewPlan()
    result = await evaluator.evaluate(_context(plan1), _question(), "yes")
    assert result.verdict == Verdict.WEAK
    assert result.strategy == FollowUpStrategy.SIMPLIFY
    assert plan1.assessment.get_topic("Embeddings Explained").bare_claims == 0

    plan2 = InterviewPlan()
    result2 = await evaluator.evaluate(_context(plan2), _question(), "yeah")
    assert result2.strategy == FollowUpStrategy.SIMPLIFY

    plan3 = InterviewPlan()
    result3 = await evaluator.evaluate(_context(plan3), _question(), "I know")
    assert result3.strategy == FollowUpStrategy.VERIFY


@pytest.mark.asyncio
async def test_greeting_never_misroutes_substantive_answer() -> None:
    """A real answer that merely starts with a greeting word must not be
    treated as a non-answer."""
    llm = LLMService(settings)
    prompts = PromptBuilder(settings)
    evaluator = ResponseEvaluator(llm, prompts)
    plan = InterviewPlan()

    result = await evaluator.evaluate(
        _context(plan),
        _question(),
        "Hi, embeddings convert text into vectors so similar meanings sit "
        "close together, which is what makes similarity search possible.",
    )
    assert result.strategy != FollowUpStrategy.SIMPLIFY
    assert result.verdict != Verdict.WEAK


@pytest.mark.asyncio
async def test_wrong_answer_detected_and_probed() -> None:
    """A recognizable misconception must be marked wrong and probed (the
    mock evaluator detects it deterministically; the real LLM judges
    correctness directly)."""
    llm = LLMService(settings)
    prompts = PromptBuilder(settings)
    evaluator = ResponseEvaluator(llm, prompts)
    plan = InterviewPlan()

    result = await evaluator.evaluate(
        _context(plan),
        _question(),
        "Embeddings are just storing the original text in a big table, so we "
        "can use SQL LIKE queries to find similar chunks.",
    )
    assert result.verdict == Verdict.WRONG
    assert result.strategy == FollowUpStrategy.RECOVERY
    assert not result.mastered_topic

    # A *criticism* of the misconception is not a misconception.
    result2 = await evaluator.evaluate(
        _context(plan),
        _question(),
        "I wouldn't use SQL LIKE for semantic search — embeddings are what "
        "capture meaning, so I'd compare vectors with cosine distance.",
    )
    assert result2.verdict != Verdict.WRONG


@pytest.mark.asyncio
async def test_idk_recovery_answer_resets_failures() -> None:
    """A good recovery answer after IDK resets the failure counter."""
    llm = LLMService(settings)
    prompts = PromptBuilder(settings)
    evaluator = ResponseEvaluator(llm, prompts)
    plan = InterviewPlan()

    await evaluator.evaluate(_context(plan), _question(), "I don't know")
    strong = (
        "The main job is to map text chunks into numeric vectors so that "
        "semantically similar pieces of text end up near each other in the "
        "vector space, which is what powers similarity search over the "
        "knowledge base."
    )
    r2 = await evaluator.evaluate(_context(plan), _question(), strong)
    assessment = plan.assessment.get_topic("Embeddings Explained")
    assert assessment.consecutive_failures == 0
    # A good recovery answer restores confidence.
    assert assessment.confidence in ("medium", "high")
    assert r2.verdict in (Verdict.GOOD, Verdict.EXCELLENT)


# ---------------------------------------------------------------------------
# planner: objective grounding + rotation
# ---------------------------------------------------------------------------


def _retriever() -> CurriculumRetriever:
    curriculum = CurriculumLoader(FIXTURES_DIR)
    curriculum.load()
    return CurriculumRetriever(curriculum)


def _profile(candidate_id: str = "CAND-001") -> CandidateProfile:
    candidates = CandidateLoader(FIXTURES_DIR)
    candidates.load()
    return CandidateAnalyzer().analyze(candidates.get(candidate_id))


@pytest.mark.asyncio
async def test_question_grounded_in_learning_objective() -> None:
    retriever = _retriever()
    llm = LLMService(settings)
    prompts = PromptBuilder(settings)
    planner = QuestionPlanner(llm, prompts, retriever)
    profile = _profile()
    plan = InterviewPlan()

    question = await planner.generate_next_question(
        _context(plan, profile), profile, plan, 0
    )
    day = retriever.get_day(question.day_index)
    assert day is not None
    assert question.learning_objective in day.objectives
    assert question.concept
    assert question.concept != day.title  # a concept, never the day label
    assert question.intent  # purpose is recorded
    # The mock question must never be a "What is <Day title>?" template.
    assert question.question.strip().lower().startswith("what is") is False
    assert day.title not in question.question


def test_select_objective_rotates_within_day() -> None:
    """Objectives on the same day are never repeated."""
    retriever = _retriever()
    planner = QuestionPlanner(None, None, retriever)  # type: ignore[arg-type]
    day_index = retriever.day_index_by_number(1)
    assert day_index is not None
    day = retriever.get_day(day_index)
    assert day is not None
    assert len(day.objectives) >= 2, "fixture day 1 should have objectives"

    plan = InterviewPlan()
    seen: list[str] = []
    for _ in range(min(3, len(day.objectives))):
        objective, _concept = planner._select_objective(day_index, plan)
        assert objective not in seen
        seen.append(objective)
        plan.questions.append(
            PlannedQuestion(
                day_index=day_index,
                day_title=day.title,
                topic=day.primary_topic,
                question_type=QuestionType.CONCEPTUAL,
                difficulty=Difficulty.MEDIUM,
                question="dummy",
                learning_objective=objective,
            )
        )


@pytest.mark.asyncio
async def test_mock_questions_never_quote_day_title() -> None:
    """Mock questions must not quote the day title in any form."""
    retriever = _retriever()
    llm = LLMService(settings)
    prompts = PromptBuilder(settings)
    planner = QuestionPlanner(llm, prompts, retriever)
    profile = _profile()
    plan = InterviewPlan()

    for index in range(5):
        question = await planner.generate_next_question(
            _context(plan, profile), profile, plan, index
        )
        day = retriever.get_day(question.day_index)
        assert day is not None
        assert day.title not in question.question
        assert "'" + day.title + "'" not in question.question
        plan.questions.append(question)
        if question.day_index not in plan.days_covered:
            plan.days_covered.append(question.day_index)


# ---------------------------------------------------------------------------
# repeated "I know" claims -> insufficient evidence -> move on
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_repeated_bare_claims_move_on() -> None:
    """Two consecutive bare claims on the same topic never become evidence:
    after the second one the interviewer stops probing and moves on, and the
    topic is marked insufficient evidence — not demonstrated."""
    llm = LLMService(settings)
    prompts = PromptBuilder(settings)
    evaluator = ResponseEvaluator(llm, prompts)
    plan = InterviewPlan()

    r1 = await evaluator.evaluate(_context(plan), _question(), "I know")
    assert r1.strategy == FollowUpStrategy.VERIFY

    r2 = await evaluator.evaluate(_context(plan), _question(), "Yes, I know that")
    assert r2.strategy == FollowUpStrategy.NEXT_TOPIC
    assessment = plan.assessment.get_topic("Embeddings Explained")
    assert assessment.bare_claims == 2
    assert assessment.knowledge_status == "insufficient_evidence"
    assert assessment.consecutive_failures == 0  # claims are not failures either
    assert assessment.confidence == "unknown"


# ---------------------------------------------------------------------------
# evidence-based early termination
# ---------------------------------------------------------------------------


def test_should_terminate_evidence_based_early() -> None:
    """When every touched topic is settled (no open failures, no bare
    claims, no unknowns) the interview ends even before the soft budget."""
    from agents.interview_manager import InterviewManager
    from config import settings
    from memory.conversation_memory import ConversationMemory
    from models.session import InterviewSession

    profile = _profile("CAND-002")
    retriever = _retriever()
    manager = InterviewManager.__new__(InterviewManager)
    manager._settings = settings

    session = InterviewSession(
        session_id="s-evidence",
        candidate_id="CAND-002",
        profile=profile,
        plan=InterviewPlan(),
        memory=ConversationMemory(),
    )
    for index in range(8):
        day = retriever.get_day(index % 4)
        session.plan.questions.append(
            PlannedQuestion(
                day_index=index % 4,
                day_title=day.title,
                topic=day.primary_topic,
                question_type=QuestionType.CONCEPTUAL,
                difficulty=Difficulty.MEDIUM,
                question="dummy",
            )
        )
        if index % 4 not in session.plan.days_covered:
            session.plan.days_covered.append(index % 4)
        # Every touched topic is settled: demonstrated, no open issues.
        assessment = session.plan.assessment.get_topic(day.primary_topic)
        assessment.questions_asked += 1
        assessment.confidence = "high"
        assessment.best_score = 8
        assessment.evidence.append("score 8/10")

    # 8 questions / 4 days, all settled -> end early (below the 12 budget).
    assert manager._should_terminate(session) is True


def test_should_terminate_keeps_going_with_open_evidence() -> None:
    """Open evidence (an unknown topic, a failure, or a bare claim) prevents
    early termination even when the minimums are met."""
    from agents.interview_manager import InterviewManager
    from config import settings
    from memory.conversation_memory import ConversationMemory
    from models.session import InterviewSession

    profile = _profile("CAND-002")
    retriever = _retriever()
    manager = InterviewManager.__new__(InterviewManager)
    manager._settings = settings

    def build() -> InterviewSession:
        session = InterviewSession(
            session_id="s-open",
            candidate_id="CAND-002",
            profile=profile,
            plan=InterviewPlan(),
            memory=ConversationMemory(),
        )
        for index in range(8):
            day = retriever.get_day(index % 4)
            session.plan.questions.append(
                PlannedQuestion(
                    day_index=index % 4,
                    day_title=day.title,
                    topic=day.primary_topic,
                    question_type=QuestionType.CONCEPTUAL,
                    difficulty=Difficulty.MEDIUM,
                    question="dummy",
                )
            )
            if index % 4 not in session.plan.days_covered:
                session.plan.days_covered.append(index % 4)
            assessment = session.plan.assessment.get_topic(day.primary_topic)
            assessment.questions_asked += 1
            assessment.best_score = 8
            assessment.confidence = "medium"  # evaluator sets this with scores
        return session

    def mark(session: InterviewSession, field: str, value) -> None:
        assessment = session.plan.assessment.get_topic(
            retriever.get_day(0).primary_topic
        )
        setattr(assessment, field, value)
        assessment.evidence.append("score 8/10")

    # Unknown status (no confidence, no evidence weight) -> keep going.
    s_unknown = build()
    mark(s_unknown, "confidence", "unknown")
    assert manager._should_terminate(s_unknown) is False

    # A single open failure (mid-ladder) -> keep going.
    s_fail = build()
    mark(s_fail, "consecutive_failures", 1)
    assert manager._should_terminate(s_fail) is False

    # A bare claim (not yet exhausted) -> keep going.
    s_claim = build()
    mark(s_claim, "bare_claims", 1)
    assert manager._should_terminate(s_claim) is False

    # Exhausted topic (moved on after two failures) -> settled -> end early.
    s_exhausted = build()
    mark(s_exhausted, "consecutive_failures", 2)
    assert manager._should_terminate(s_exhausted) is True


def test_should_terminate_all_idk_ends_at_minimum() -> None:
    """An all-\"I don't know\" interview finishes as soon as the minimums are
    met: every topic is exhausted (moved on after two failures), so the
    engine must NOT drag it to the soft target with topic revisits."""
    from agents.interview_manager import InterviewManager
    from config import settings
    from memory.conversation_memory import ConversationMemory
    from models.session import InterviewSession

    profile = _profile("CAND-002")
    retriever = _retriever()
    manager = InterviewManager.__new__(InterviewManager)
    manager._settings = settings

    session = InterviewSession(
        session_id="s-idk",
        candidate_id="CAND-002",
        profile=profile,
        plan=InterviewPlan(),
        memory=ConversationMemory(),
    )
    for index in range(8):
        day = retriever.get_day(index % 6)
        session.plan.questions.append(
            PlannedQuestion(
                day_index=index % 6,
                day_title=day.title,
                topic=day.primary_topic,
                question_type=QuestionType.CONCEPTUAL,
                difficulty=Difficulty.MEDIUM,
                question="dummy",
            )
        )
        if index % 6 not in session.plan.days_covered:
            session.plan.days_covered.append(index % 6)
        assessment = session.plan.assessment.get_topic(day.primary_topic)
        assessment.questions_asked += 1
        assessment.consecutive_failures = 2  # exhausted -> moved on
        assessment.confidence = "low"
        assessment.evidence.append("score 2/10 (weak)")

    assert manager._should_terminate(session) is True


# ---------------------------------------------------------------------------
# feedback topic synchronisation (never "0 topics")
# ---------------------------------------------------------------------------


def test_feedback_prompt_lists_every_touched_topic() -> None:
    """The feedback prompt must include every topic the interviewer touched
    — including ones with no demonstrated evidence — so the mock/LLM cannot
    report fewer topics than the transcript contains."""
    from services.prompt_builder import PromptBuilder

    prompts = PromptBuilder(settings)
    plan = InterviewPlan()
    profile = _profile()
    manager = ContextManager()
    context = manager.build(
        state=InterviewState.EVALUATION,
        candidate=profile,
        plan=plan,
        memory=ConversationMemory(),
        question_index=0,
    )
    # Touch two topics; one produced evidence, one only "I don't know".
    touched = plan.assessment.get_topic("Python Fundamentals")
    touched.questions_asked = 1
    touched.evidence.append("score 2/10 (weak)")
    touched.confidence = "low"
    claim = plan.assessment.get_topic("Web API Development")
    claim.questions_asked = 1
    claim.bare_claims = 1

    prompt = prompts.feedback_prompt(context)
    assert "Python Fundamentals" in prompt
    assert "Web API Development" in prompt
    assert "knowledge_status=insufficient_evidence" in prompt
    assert "knowledge_status=" in prompt
    # No topic was silently dropped.
    assert "No topic could be confidently assessed" not in prompt


@pytest.mark.asyncio
async def test_feedback_topics_match_interview_state() -> None:
    """A full interview's feedback must report at least as many curriculum
    topics as the state recorded (regression for the "0 topics" bug)."""
    from agents.interview_manager import InterviewManager
    from agents.candidate_analyzer import CandidateAnalyzer
    from agents.difficulty_manager import DifficultyManager
    from agents.feedback_generator import FeedbackGenerator
    from agents.followup_generator import FollowUpGenerator
    from agents.response_evaluator import ResponseEvaluator
    from memory.context_manager import ContextManager
    from memory.conversation_memory import ConversationMemory
    from models.session import InterviewSession
    from retrieval.candidate_loader import CandidateLoader
    from services.session_manager import SessionManager

    candidates = CandidateLoader(FIXTURES_DIR)
    candidates.load()
    curriculum = CurriculumLoader(FIXTURES_DIR)
    curriculum.load()
    retriever = CurriculumRetriever(curriculum)
    profile = CandidateAnalyzer().analyze(candidates.get("CAND-001"))

    llm = LLMService(settings)
    prompts = PromptBuilder(settings)
    difficulty = DifficultyManager()
    planner = QuestionPlanner(llm, prompts, retriever, difficulty_manager=difficulty)
    evaluator = ResponseEvaluator(llm, prompts)
    followups = FollowUpGenerator(llm, prompts, retriever, difficulty_manager=difficulty)
    feedback_generator = FeedbackGenerator(llm, prompts)
    manager = InterviewManager.__new__(InterviewManager)
    manager._settings = settings
    manager._planner = planner
    manager._evaluator = evaluator
    manager._followups = followups
    manager._feedback_generator = feedback_generator
    manager._prompts = prompts
    manager._retriever = retriever
    manager._context = ContextManager()

    session = InterviewSession(
        session_id="s-feedback",
        candidate_id="CAND-001",
        profile=profile,
        plan=planner.build_plan(profile),
        memory=ConversationMemory(),
    )
    # Drive 8 main questions with weak answers (never terminating early).
    for index in range(8):
        question = await planner.generate_next_question(
            manager._context.build(
                state=InterviewState.QUESTIONING,
                candidate=profile,
                plan=session.plan,
                memory=session.memory,
                question_index=index,
            ),
            profile,
            session.plan,
            index,
        )
        session.plan.questions.append(question)
        if question.day_index not in session.plan.days_covered:
            session.plan.days_covered.append(question.day_index)
        context = manager._context.build(
            state=InterviewState.QUESTIONING,
            candidate=profile,
            plan=session.plan,
            memory=session.memory,
            question_index=index,
            last_answer="I don't know",
        )
        evaluation = await manager._evaluator.evaluate(
            context, question, "I don't know"
        )
        session.memory.add_turn(
            question=question.question,
            topic=question.topic,
            day_index=question.day_index,
            question_type=question.question_type,
            difficulty=question.difficulty,
            answer="I don't know",
            score=evaluation.score,
            verdict=evaluation.verdict,
            follow_up=evaluation.strategy,
            notes=evaluation.notes,
        )

    assert len(session.plan.days_covered) >= 4
    touched = sum(
        1 for a in session.plan.assessment.topics.values() if a.touched
    )
    assert touched >= 4

    feedback = await manager._feedback_generator.generate(
        manager._context.build(
            state=InterviewState.EVALUATION,
            candidate=profile,
            plan=session.plan,
            memory=session.memory,
            question_index=0,
        )
    )
    # The authoritative list is never empty and matches the touched topics.
    assert len(feedback.topics_covered) == touched
    # The mock summary reports the actual covered count (was "0 topics").
    assert str(touched) in feedback.summary
    assert "0 curriculum topics" not in feedback.summary


def test_feedback_score_gated_by_evidence() -> None:
    """A 0/10 average can never produce an unexplained 30/100: the coverage
    term is gated by demonstrated quality, so no evidence -> no score."""
    from agents.feedback_generator import FeedbackGenerator
    from memory.conversation_memory import ConversationMemory

    plan = InterviewPlan()
    plan.days_covered = [0, 1, 2, 3, 4]
    memory = ConversationMemory()
    for index in range(5):
        memory.add_turn(
            question="q",
            topic=f"Topic {index}",
            day_index=index,
            question_type=QuestionType.CONCEPTUAL,
            difficulty=Difficulty.MEDIUM,
            answer="I don't know",
            score=0,
            verdict=Verdict.WEAK,
            follow_up=FollowUpStrategy.NEXT_TOPIC,
        )
    context = ContextManager().build(
        state=InterviewState.EVALUATION,
        candidate=_profile(),
        plan=plan,
        memory=memory,
        question_index=0,
    )
    generator = FeedbackGenerator(LLMService(settings), PromptBuilder(settings))
    metrics = generator.compute_internal_metrics(context)
    assert metrics.score < 10, f"0/10 average produced {metrics.score}/100"

    # With real evidence the same coverage yields a proportionally high score.
    memory2 = ConversationMemory()
    for index in range(5):
        memory2.add_turn(
            question="q",
            topic=f"Topic {index}",
            day_index=index,
            question_type=QuestionType.CONCEPTUAL,
            difficulty=Difficulty.MEDIUM,
            answer="strong answer",
            score=9,
            verdict=Verdict.EXCELLENT,
            follow_up=FollowUpStrategy.NEXT_TOPIC,
        )
    context2 = ContextManager().build(
        state=InterviewState.EVALUATION,
        candidate=_profile(),
        plan=plan,
        memory=memory2,
        question_index=0,
    )
    metrics2 = generator.compute_internal_metrics(context2)
    assert metrics2.score >= 80


def test_mock_feedback_score_gated_by_evidence() -> None:
    """The mock feedback score follows the same evidence gate (0/10 average
    -> ~0, not an unexplained 30)."""
    from services.llm_service import MockProvider

    user = (
        "ASSESSMENT STATE (per-topic, derived from the actual interview)\n"
        "- Topic A: knowledge_status=incorrect, confidence=low, failures=2, bare_claims=0, score range 0-0/10\n"
        "- Topic B: knowledge_status=incorrect, confidence=low, failures=2, bare_claims=0, score range 0-0/10\n"
        "PROFILE TOPICS NOT TESTED\nnone\n"
        "FULL INTERVIEW TRANSCRIPT\n"
        "[Q1] Topic A | score=0/10 verdict=weak\n"
        "[Q2] Topic B | score=0/10 verdict=weak\n"
        "CANDIDATE PROFILE\nTest candidate"
    )
    feedback = MockProvider()._mock_feedback(user)
    assert feedback["score"] < 10, f"0/10 average produced {feedback['score']}"


# ---------------------------------------------------------------------------
# conversational bridge: reaction + transition + question
# ---------------------------------------------------------------------------


def _bridge(question: str = "Can you explain vector embeddings?", **kwargs) -> str:
    return PromptBuilder(settings).next_question_bridge(
        question, **kwargs
    )


def test_bridge_always_contains_the_question() -> None:
    """Whatever the reaction/transition rotation picks, the question itself
    is always present verbatim."""
    question = "Can you explain vector embeddings?"
    for index in range(12):
        for verdict in (None, "good", "weak", "wrong", "unclear"):
            text = _bridge(question, index=index, last_verdict=verdict)
            assert text.endswith(question)
            assert question in text


def test_bridge_reaction_matches_verdict() -> None:
    """The reaction pool is keyed by the previous answer's verdict."""
    good = _bridge(index=0, last_verdict="good")
    weak = _bridge(index=0, last_verdict="weak")
    wrong = _bridge(index=0, last_verdict="wrong")
    claim = _bridge(index=0, last_verdict="unclear")
    assert any(good.startswith(g) for g in ("Good", "Nice", "Right", "Exactly", "That's", "Good thinking"))
    assert any(weak.startswith(w) for w in ("No worries", "That's okay", "Let's try", "Alright"))
    assert any(wrong.startswith(w) for w in ("I see", "There's a subtlety", "Let's look"))
    assert any(claim.startswith(c) for c in ("Alright", "Fair enough", "Okay"))


def test_bridge_reactions_rotate() -> None:
    """Consecutive bridges on the same verdict use different reactions (no
    repeated stock phrase)."""
    seen = {
        _bridge(index=i, last_verdict="good")[:20]
        for i in range(0, 20, 3)
    }
    assert len(seen) >= 2


def test_bridge_sometimes_has_no_reaction() -> None:
    """Human rhythm: not every turn reacts to the previous answer (the
    reaction pool is skipped on a rotation even for good answers), but the
    question is always asked."""
    reactions = ("Good", "Nice", "Right", "Exactly", "That's", "Good thinking")
    bare = _bridge(index=2, last_verdict="good")
    assert not bare.startswith(reactions)
    assert bare.endswith("Can you explain vector embeddings?")


def test_bridge_new_topic_transition_is_topic_free() -> None:
    """Transitions never announce the curriculum topic title: the
    interviewer says \"let's switch gears\", not \"let's talk about
    Security, Privacy & Guardrails\"."""
    topic = "Security, Privacy & Guardrails"
    for index in range(12):
        for verdict in (None, "good", "weak", "wrong", "unclear"):
            text = _bridge(
                "What would you monitor in production?",
                index=index,
                last_verdict=verdict,
                next_topic=topic,
                related=False,
            )
            assert topic not in text
            assert text.endswith("What would you monitor in production?")


def test_bridge_never_uses_banned_phrases() -> None:
    """The deterministic bridge must never emit the robotic stock phrases."""
    banned = (
        "Glad to hear it",
        "Let's make sure we're on the same page",
        "No problem — let's ground this differently",
        "You mentioned",
        "Let's move on to the next topic",
    )
    for index in range(24):
        for verdict in (None, "good", "weak", "wrong", "unclear"):
            text = _bridge(index=index, last_verdict=verdict, next_topic="MCP")
            for phrase in banned:
                assert phrase.lower() not in text.lower()


def test_bridge_same_topic_uses_deepen_transition() -> None:
    """Staying on the same topic deepens instead of switching gears."""
    text = _bridge(index=4, last_verdict="good", next_topic="Embeddings", same_topic=True)
    assert "deeper" in text or "stay on" in text or text.endswith("Can you explain vector embeddings?")


def test_bridge_never_leaks_comment_lines() -> None:
    """Rotation pools must never leak messages.md comment lines into the
    interviewer's reply (regression: comments between sections used to
    become pool entries)."""
    from services.prompt_builder import PromptBuilder

    prompts = PromptBuilder(settings)
    for pool_name in ("reaction_good", "reaction_recovery", "reaction_weak",
                      "reaction_weak2", "reaction_weak3", "reaction_claim",
                      "reaction_claim2", "reaction_wrong", "transition_related",
                      "transition_new", "transition_same"):
        for entry in prompts._pool(pool_name):
            assert not entry.startswith("#"), f"{pool_name} leaked: {entry!r}"
    for index in range(24):
        for verdict in (None, "good", "weak", "wrong", "unclear"):
            text = _bridge(index=index, last_verdict=verdict, next_topic="MCP")
            assert "#" not in text
            assert "Transitions when" not in text


def test_mock_simplify_never_uses_core_job() -> None:
    """The mock simplify follow-up must never fall back to the universal
    \"what's the core job of X?\" template (with broken gerund grammar for
    verbs like \"Secure …\")."""
    from services.llm_service import MockProvider

    mock = MockProvider()
    for _ in range(6):
        out = mock._mock_follow_up(
            "- Follow-up strategy: simplify\n"
            "- Learning objective: Secure chatbot APIs against unauthorized access\n"
            "- Technical concept: how to secure chatbot APIs against unauthorized access\n"
            "CANDIDATE'S ANSWER\nI don't know\n\nEVALUATION\nweak",
            "Security",
        )
        assert "core job" not in out["question"].lower()
        assert "simpler angle" not in out["question"].lower()
        assert "in one sentence" not in out["question"].lower()


def test_mock_feedback_no_false_engaged_strength() -> None:
    """An all-\"I don't know\" interview must never produce an \"Engaged with
    every question\" strength nor a false competence claim: the fallback
    strength is truthful, and the gaps/summary carry the lack of evidence."""
    from services.llm_service import MockProvider

    user = (
        "ASSESSMENT STATE (per-topic, derived from the actual interview)\n"
        "- Embeddings Explained: knowledge_status=incorrect, confidence=low, failures=2, bare_claims=0, score range 2-2/10\n"
        "- Vector Databases: knowledge_status=incorrect, confidence=low, failures=2, bare_claims=0, score range 2-2/10\n"
        "PROFILE TOPICS NOT TESTED\nnone\n"
        "FULL INTERVIEW TRANSCRIPT\n"
        "[Q1] Embeddings Explained | score=2/10 verdict=weak\n"
        "[Q2] Vector Databases | score=2/10 verdict=weak\n"
        "CANDIDATE PROFILE\nTest candidate"
    )
    feedback = MockProvider()._mock_feedback(user)
    strengths = " ".join(feedback["strengths"]).lower()
    assert "engaged with every question" not in strengths
    assert "demonstrated" not in strengths
    assert feedback["strengths"]  # schema requires >= 1
    assert feedback["gaps"]  # weak topics must appear as gaps
    assert "did not demonstrate" in feedback["summary"]


# ---------------------------------------------------------------------------
# LLM-generated content-aware reaction (pools are only a fallback)
# ---------------------------------------------------------------------------


def _fallback_reaction(question: str = "Can you explain vector embeddings?", **kwargs) -> str:
    return PromptBuilder(settings).reaction_or_fallback(
        question, topic="Embeddings", index=0, **kwargs
    )


def test_reaction_or_fallback_keeps_valid_reaction() -> None:
    """A content-aware LLM reaction passes through unchanged."""
    reaction = "That's the piece I was after — hybrid search for exact IDs."
    assert _fallback_reaction(reaction) == reaction


def test_reaction_or_fallback_rejects_canned_phrases() -> None:
    """Canned acknowledgement phrases never reach the candidate: they fall
    back to the (neutral, varied) deterministic pools."""
    for canned in (
        "Glad to hear it — let's move on.",
        "Let's try a simpler angle.",
        "You mentioned Docker earlier.",
        "Based on your previous answer, what's the core job of X?",
    ):
        fallback = _fallback_reaction(canned, last_verdict="good")
        assert fallback != canned
        assert not any(
            phrase in fallback.lower()
            for phrase in ("glad to hear", "simpler angle", "you mentioned",
                           "core job", "based on your previous")
        )
        assert fallback  # a reaction is still produced


def test_reaction_or_fallback_rejects_metadata_leak() -> None:
    """A reaction must never quote the curriculum topic title or a day
    number — those fall back to the pools too."""
    fallback = _fallback_reaction(
        "Let's talk about Day 27 — Security, Privacy & Guardrails.",
        last_verdict="weak",
    )
    assert "Security, Privacy & Guardrails" not in fallback
    assert "Day 27" not in fallback


def test_reaction_or_fallback_empty_uses_pool() -> None:
    """Empty reaction -> deterministic pool reaction (fallback path)."""
    reaction = _fallback_reaction("", last_verdict="good")
    assert any(
        reaction.startswith(g)
        for g in ("Good", "Nice", "Right", "Exactly", "That's", "Good thinking")
    )


def test_memory_firmness_and_emotion() -> None:
    """The interviewer state derives from the conversation: firmness and
    emotion escalate with repeated non-answers and reset on a strong answer,
    and a recovery is recognized."""
    memory = ConversationMemory()

    def add(verdict: Verdict, topic: str = "RAG", score: int = 2) -> None:
        memory.add_turn(
            question="q",
            topic=topic,
            day_index=0,
            question_type=QuestionType.CONCEPTUAL,
            difficulty=Difficulty.MEDIUM,
            answer="answer",
            score=score,
            verdict=verdict,
            follow_up=FollowUpStrategy.NEXT_TOPIC,
        )

    assert memory.firmness == 0
    assert memory.interviewer_emotion == "neutral"
    add(Verdict.WEAK)
    assert memory.firmness == 1
    assert memory.interviewer_emotion == "concerned"
    add(Verdict.WEAK)
    assert memory.firmness == 2
    assert memory.interviewer_emotion == "mildly_frustrated"
    add(Verdict.UNCLEAR)
    assert memory.firmness == 3
    assert memory.interviewer_emotion == "firm"
    # A strong answer resets firmness and recognizes the recovery.
    add(Verdict.EXCELLENT, score=9)
    assert memory.firmness == 0
    assert memory.recovered is True
    assert memory.interviewer_emotion == "relieved"


def test_mock_question_reaction_content_seeded() -> None:
    """The mock's reaction acknowledges the previous answer's substance
    (seeded by its content) and escalates with firmness for non-answers."""
    from services.llm_service import MockProvider

    mock = MockProvider()
    substantive = mock._mock_question(
        "question 3 of 10\n- Consecutive weak answers so far: 0\n"
        "CANDIDATE'S PREVIOUS ANSWER\n"
        "We would embed each chunk and compare vectors with cosine similarity.\n\n"
        "PREVIOUS QUESTIONS ASKED\nnone\n- Question type: conceptual\n"
        "- Learning objective: Store embeddings in a vector store\n"
        "- Technical concept: how to store embeddings",
        "Vector Databases",
    )
    assert substantive["reaction"]
    assert any(
        substantive["reaction"].startswith(r)
        for r in ("That's a useful angle", "Good —", "Right,", "Yeah —")
    )
    # Non-substantive answer + high streak -> firmer reaction.
    firm = mock._mock_question(
        "question 6 of 10\n- Consecutive weak answers so far: 4\n"
        "CANDIDATE'S PREVIOUS ANSWER\nI don't know\n\n"
        "PREVIOUS QUESTIONS ASKED\nnone\n- Question type: conceptual\n"
        "- Learning objective: Store embeddings in a vector store\n"
        "- Technical concept: how to store embeddings",
        "Vector Databases",
    )
    gentle = mock._mock_question(
        "question 6 of 10\n- Consecutive weak answers so far: 0\n"
        "CANDIDATE'S PREVIOUS ANSWER\nI don't know\n\n"
        "PREVIOUS QUESTIONS ASKED\nnone\n- Question type: conceptual\n"
        "- Learning objective: Store embeddings in a vector store\n"
        "- Technical concept: how to store embeddings",
        "Vector Databases",
    )
    assert any(
        firm["reaction"].startswith(r)
        for r in ("I've tried this a couple of ways now", "Alright, let's leave")
    )
    assert any(
        gentle["reaction"].startswith(r) for r in ("No worries", "That's okay")
    )


def test_should_terminate_total_questions_cap() -> None:
    """The 12-question safety ceiling applies to ACTUAL questions (mains +
    follow-ups), so a follow-up-dense interview cannot exceed it even before
    the 10-main soft target."""
    from agents.interview_manager import InterviewManager
    from memory.conversation_memory import ConversationMemory
    from models.session import InterviewSession

    retriever = _retriever()
    profile = _profile("CAND-002")
    manager = InterviewManager.__new__(InterviewManager)
    manager._settings = settings

    session = InterviewSession(
        session_id="s-cap",
        candidate_id="CAND-002",
        profile=profile,
        plan=InterviewPlan(),
        memory=ConversationMemory(),
    )
    for index in range(8):
        day = retriever.get_day(index % 4)
        session.plan.questions.append(
            PlannedQuestion(
                day_index=index % 4,
                day_title=day.title,
                topic=day.primary_topic,
                question_type=QuestionType.CONCEPTUAL,
                difficulty=Difficulty.MEDIUM,
                question="dummy",
            )
        )
        if index % 4 not in session.plan.days_covered:
            session.plan.days_covered.append(index % 4)
        session.plan.assessment.get_topic(day.primary_topic).questions_asked += 1

    topic0 = session.plan.assessment.get_topic(retriever.get_day(0).primary_topic)
    # 8 mains + 4 follow-ups = 12 actual questions -> ceiling fires.
    topic0.follow_ups = 4
    assert manager._should_terminate(session) is True

    # 8 mains + 2 follow-ups = 10 actual -> soft target (10) fires.
    topic0.follow_ups = 2
    assert manager._should_terminate(session) is True

    # 8 mains + 1 follow-up = 9 actual -> neither cap nor soft target, and
    # no evidence is settled -> keep going.
    topic0.follow_ups = 1
    assert manager._should_terminate(session) is False


# ---------------------------------------------------------------------------
# emotional trajectory: escalating firmness + recovery acknowledgment
# ---------------------------------------------------------------------------


def test_memory_consecutive_weak_streak() -> None:
    """The memory tracks the trailing streak of non-substantive answers
    (weak / bare-claim verdicts); a good answer resets it."""
    memory = ConversationMemory()

    def add(verdict: Verdict, answer: str = "answer") -> None:
        memory.add_turn(
            question="q",
            topic="RAG",
            day_index=0,
            question_type=QuestionType.CONCEPTUAL,
            difficulty=Difficulty.MEDIUM,
            answer=answer,
            score=2 if verdict in (Verdict.WEAK, Verdict.UNCLEAR) else 8,
            verdict=verdict,
            follow_up=FollowUpStrategy.NEXT_TOPIC,
        )

    assert memory.consecutive_weak == 0
    add(Verdict.WEAK, "I don't know")
    assert memory.consecutive_weak == 1
    add(Verdict.UNCLEAR, "I know")
    assert memory.consecutive_weak == 2
    # A demonstrated answer breaks the streak.
    add(Verdict.GOOD)
    assert memory.consecutive_weak == 0


def test_bridge_weak_reaction_escalates_with_streak() -> None:
    """Repeated weak answers make the interviewer's reaction progressively
    firmer (mild -> direct -> firm), like a human interviewer who has tried
    a concept a couple of ways."""
    mild = _bridge(index=0, last_verdict="weak", consecutive_weak=1)
    direct = _bridge(index=1, last_verdict="weak", consecutive_weak=2)
    firm = _bridge(index=4, last_verdict="weak", consecutive_weak=4)
    mild_pool = ("No worries", "That's okay", "Let's come at it another way",
                 "Alright, let's keep it simple")
    direct_pool = ("Alright, let's make this one easier",
                   "Okay, let's slow down", "Let's take a step back")
    firm_pool = ("I've tried this a couple of ways now",
                 "Alright, let's leave that one for now",
                 "Let's move past this one")
    assert any(mild.startswith(w) for w in mild_pool)
    assert any(direct.startswith(w) for w in direct_pool)
    assert any(firm.startswith(w) for w in firm_pool)


def test_bridge_claim_reaction_escalates() -> None:
    """Repeated bare claims ("I know") get a firmer, more skeptical reaction
    instead of the same neutral "Alright — " every time."""
    first = _bridge(index=0, last_verdict="unclear", consecutive_weak=1)
    repeated = _bridge(index=1, last_verdict="unclear", consecutive_weak=2)
    assert any(
        first.startswith(c) for c in ("Alright", "Fair enough", "Okay")
    )
    assert any(
        repeated.startswith(c)
        for c in ("Fair enough — but I still need the answer itself",
                  "Alright — I can't mark that without seeing it",
                  "Okay — then let's see it in action")
    )


def test_bridge_recovery_reaction() -> None:
    """A good answer on a topic the candidate previously struggled with gets
    an explicit recovery acknowledgment ("Much better — ")."""
    text = _bridge(index=0, last_verdict="good", recovered=True)
    assert any(
        text.startswith(r)
        for r in ("Much better", "Yes, that's closer", "Good recovery",
                  "That's more like it")
    )
    # Without a prior struggle, a good answer uses the normal reaction.
    normal = _bridge(index=0, last_verdict="good")
    assert not any(
        normal.startswith(r)
        for r in ("Much better", "Yes, that's closer", "Good recovery",
                  "That's more like it")
    )


def test_question_prompt_includes_full_conversation() -> None:
    """The question generator receives the FULL conversation (earlier
    questions AND answers), not just the last answer — it must be able to
    remember earlier claims, mistakes and examples."""
    from models.question_intent import QuestionIntent
    from services.prompt_builder import PromptBuilder

    prompts = PromptBuilder(settings)
    memory = ConversationMemory()
    memory.add_turn(
        question="What is RAG?",
        topic="RAG",
        day_index=0,
        question_type=QuestionType.CONCEPTUAL,
        difficulty=Difficulty.MEDIUM,
        answer="RAG retrieves documents before generation.",
        score=8,
        verdict=Verdict.GOOD,
        follow_up=FollowUpStrategy.NEXT_TOPIC,
    )
    memory.add_turn(
        question="How does it decide which documents are relevant?",
        topic="RAG",
        day_index=0,
        question_type=QuestionType.CONCEPTUAL,
        difficulty=Difficulty.MEDIUM,
        answer="Using embeddings and similarity search.",
        score=9,
        verdict=Verdict.EXCELLENT,
        follow_up=FollowUpStrategy.DEEPER,
        is_follow_up=True,
    )
    context = ContextManager().build(
        state=InterviewState.QUESTIONING,
        candidate=_profile(),
        plan=InterviewPlan(),
        memory=memory,
        question_index=2,
    )
    intent = QuestionIntent(
        curriculum_day=1,
        topic="RAG",
        module="Retrieval",
        learning_objective="Understand RAG",
        concept="how retrieval grounds generation",
        cognitive_level="application",
        purpose="test_application",
        expected_evidence=["explains retrieval"],
        difficulty="medium",
        relationship="continuing on the same curriculum day",
        candidate_signal="normal coverage",
    )
    prompt = prompts.question_prompt(
        context,
        intent=intent,
        question_type="scenario",
        difficulty="medium",
        curriculum="grounding text",
        previous_topic="RAG",
    )
    # Both earlier answers AND questions are visible to the generator.
    assert "RAG retrieves documents before generation." in prompt
    assert "Using embeddings and similarity search." in prompt
    assert "What is RAG?" in prompt
    assert "FULL CONVERSATION SO FAR" in prompt


@pytest.mark.asyncio
async def test_evaluation_contradiction_probes(monkeypatch) -> None:
    """When the LLM flags that the candidate's answer contradicts an earlier
    statement, the evaluator turns it into a gentle probe and records the
    contradiction in memory (so later turns can reference it)."""
    from schemas.llm import EvaluationDraft

    llm = LLMService(settings)
    prompts = PromptBuilder(settings)
    evaluator = ResponseEvaluator(llm, prompts)

    async def fake_completion(*, system_prompt, user_prompt, schema):
        return EvaluationDraft(
            score=7,
            verdict="good",
            follow_up="deeper",
            mastered_topic=False,
            contradiction_detected=True,
            notes=(
                "Earlier the candidate said the vector database creates the "
                "embeddings; now they say the embedding model does."
            ),
        )

    monkeypatch.setattr(llm, "structured_completion", fake_completion)
    plan = InterviewPlan()
    memory = ConversationMemory()
    context = ContextManager().build(
        state=InterviewState.QUESTIONING,
        candidate=_profile(),
        plan=plan,
        memory=memory,
        question_index=1,
    )
    result = await evaluator.evaluate(
        context,
        _question(),
        "The embedding model produces the vectors, then the vector database "
        "stores them for similarity search.",
    )
    assert result.strategy == FollowUpStrategy.PROBE
    assert result.wants_follow_up is True
    assert memory.contradictions, "contradiction must be recorded in memory"
    # The recorded note names the topic and the discrepant statements.
    assert "Embeddings Explained" in memory.contradictions[0]
    assert "embedding model" in memory.contradictions[0]


def test_mock_follow_up_escalates_when_struggling() -> None:
    """After repeated weak answers the mock follow-up stops using the gentle
    openers and becomes direct (still never "core job of X")."""
    from services.llm_service import MockProvider

    mock = MockProvider()
    out = mock._mock_follow_up(
        "- Follow-up strategy: simplify\n"
        "- Learning objective: Secure chatbot APIs against unauthorized access\n"
        "- Technical concept: how to secure chatbot APIs against unauthorized access\n"
        "- Follow-ups so far on this topic: 1\n"
        "- Consecutive weak answers so far in the interview: 4\n"
        "CANDIDATE'S ANSWER\nI don't know\n\nEVALUATION\nweak",
        "Security",
    )
    assert "core job" not in out["question"].lower()
    assert any(
        firm in out["question"]
        for firm in ("I've tried this a couple of ways now",
                     "Let's make this one easier", "one last angle")
    )
    # A single weak answer keeps the patient opener.
    gentle = mock._mock_follow_up(
        "- Follow-up strategy: simplify\n"
        "- Learning objective: Secure chatbot APIs against unauthorized access\n"
        "- Technical concept: how to secure chatbot APIs against unauthorized access\n"
        "- Follow-ups so far on this topic: 0\n"
        "- Consecutive weak answers so far in the interview: 1\n"
        "CANDIDATE'S ANSWER\nI don't know\n\nEVALUATION\nweak",
        "Security",
    )
    assert not any(
        firm in gentle["question"]
        for firm in ("I've tried this a couple of ways now",
                     "Let's make this one easier", "one last angle")
    )


def test_mock_question_occasionally_references_mentions() -> None:
    """The mock may build on a concept the candidate raised earlier, but
    never on every question, and only when the mention is relevant to the
    question's concept (never a non-sequitur)."""
    from services.llm_service import MockProvider

    mock = MockProvider()
    relevant = mock._mock_question(
        "question 5 of 10\n- Candidate mentioned earlier: vector database, Docker\n- Question type: conceptual\n- Learning objective: Store embeddings in a vector store\n- Technical concept: how to store embeddings",
        "Vector Databases",
    )
    irrelevant = mock._mock_question(
        "question 5 of 10\n- Candidate mentioned earlier: ChromaDB, Docker\n- Question type: conceptual\n- Learning objective: Store embeddings in a vector store\n- Technical concept: how to store embeddings",
        "Vector Databases",
    )
    without = mock._mock_question(
        "question 2 of 10\n- Candidate mentioned earlier: none yet\n- Question type: conceptual\n- Learning objective: Store embeddings in a vector store\n- Technical concept: how to store embeddings",
        "Vector Databases",
    )
    # Rotation: question 5 (n % 4 == 1) references a RELEVANT mention;
    # question 2 does not; ChromaDB/Docker are irrelevant to embeddings.
    assert "vector database" in relevant["question"]
    assert "mentioned" in relevant["question"]
    assert "mentioned" not in irrelevant["question"]
    assert "mentioned" not in without["question"]
