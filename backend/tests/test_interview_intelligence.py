"""Interview-intelligence regression tests.

Covers the fixes that make the interviewer assess *concepts*, not course
titles:

* concept derivation from learning objectives (never the day title),
* "I know" / "yes" is NOT competence — it triggers a verify probe,
* "I don't know" ladder: simplify -> recovery scaffold -> move on,
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

    # A repeated failure -> keep going (misconception still open).
    s_fail = build()
    mark(s_fail, "consecutive_failures", 2)
    assert manager._should_terminate(s_fail) is False

    # A bare claim -> keep going (knowledge asserted, not demonstrated).
    s_claim = build()
    mark(s_claim, "bare_claims", 1)
    assert manager._should_terminate(s_claim) is False


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
