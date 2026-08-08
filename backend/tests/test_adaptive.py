"""Adaptive interviewer behaviour tests.

* Repeated \"I don't know\" answers still lead to a completed interview that
  satisfies the 8-question / 4-day minimums without trapping the candidate,
* strong answers progress normally,
* the planner never picks uncompleted curriculum days and drops difficulty
  after repeated failures,
* the interview never terminates before the minimums are met.
"""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from main import app
from models.enums import Difficulty, QuestionType
from models.plan import InterviewPlan, PlannedQuestion
from retrieval.curriculum_loader import CurriculumLoader
from retrieval.curriculum_retriever import CurriculumRetriever
from tests.conftest import FIXTURES_DIR


def _client() -> TestClient:
    return TestClient(app)


def _run_to_completion(client: TestClient, session_id: str, answer: str) -> dict:
    data = client.post(
        "/api/interview",
        json={"sessionId": session_id, "candidate": {"member": {"id": "CAND-001"}}},
    ).json()
    days_seen = {data["currentDay"]} if data.get("currentDay") else set()
    turns = 0
    while not data["done"] and turns < 60:
        turns += 1
        data = client.post(
            "/api/interview",
            json={"sessionId": session_id, "message": answer},
        ).json()
        if data.get("currentDay"):
            days_seen.add(data["currentDay"])
        if data["state"] == "FINAL_QUESTION" and not data["done"]:
            data = client.post(
                "/api/interview",
                json={"sessionId": session_id, "message": "No questions, thank you!"},
            ).json()
    data["_days_seen"] = days_seen
    data["_turns"] = turns
    return data


def test_repeated_idk_still_covers_minimums() -> None:
    """A candidate who answers \"I don't know\" repeatedly must not trap the
    interviewer on one topic; the interview keeps moving and still covers
    8+ questions across 4+ days."""
    with _client() as client:
        session_id = str(uuid.uuid4())
        data = _run_to_completion(client, session_id, "I don't know")
        assert data["done"] is True
        assert len(data["_days_seen"]) >= 4, data["_days_seen"]
        assert data["feedback"] is not None
        snapshot = client.get(f"/api/interview/{session_id}").json()
        assert snapshot["totalQuestions"] >= 8, snapshot["totalQuestions"]


def test_strong_answers_progress_normally() -> None:
    """Long, detailed answers drive the interview to complete feedback."""
    with _client() as client:
        session_id = str(uuid.uuid4())
        strong = (
            "I would break the problem into clear components, choose the "
            "right data model, then design the interfaces between them. In "
            "production I would add monitoring, logging and automated tests, "
            "and I would weigh the trade-offs between a managed service and "
            "running it ourselves before deciding."
        )
        data = _run_to_completion(client, session_id, strong)
        assert data["done"] is True
        assert len(data["_days_seen"]) >= 4
        assert data["feedback"]["strengths"]


def test_planner_never_picks_uncompleted_days() -> None:
    """CAND-001 skipped day 6: the planner must never ask about it."""
    from agents.candidate_analyzer import CandidateAnalyzer
    from agents.question_planner import QuestionPlanner
    from retrieval.candidate_loader import CandidateLoader

    candidates = CandidateLoader(FIXTURES_DIR)
    candidates.load()
    raw = candidates.get("CAND-001")
    profile = CandidateAnalyzer().analyze(raw)
    curriculum = CurriculumLoader(FIXTURES_DIR)
    curriculum.load()
    retriever = CurriculumRetriever(curriculum)
    planner = QuestionPlanner(None, None, retriever)  # type: ignore[arg-type]

    plan = InterviewPlan()
    for _ in range(8):
        day_index, _topic = planner._determine_next_topic(profile, plan)
        day = retriever.get_day(day_index)
        assert day is not None
        assert day.day_number in profile.completed_days, day.day_number
        plan.questions.append(
            PlannedQuestion(
                day_index=day_index,
                day_title=day.title,
                topic=day.primary_topic,
                question_type=QuestionType.CONCEPTUAL,
                difficulty=Difficulty.MEDIUM,
                question="dummy",
            )
        )
        if day_index not in plan.days_covered:
            plan.days_covered.append(day_index)


def test_planner_difficulty_drops_after_failures() -> None:
    from agents.candidate_analyzer import CandidateAnalyzer
    from agents.question_planner import QuestionPlanner
    from retrieval.candidate_loader import CandidateLoader

    candidates = CandidateLoader(FIXTURES_DIR)
    candidates.load()
    profile = CandidateAnalyzer().analyze(candidates.get("CAND-002"))
    assert profile.baseline_difficulty == Difficulty.ADVANCED

    curriculum = CurriculumLoader(FIXTURES_DIR)
    curriculum.load()
    retriever = CurriculumRetriever(curriculum)
    planner = QuestionPlanner(None, None, retriever)  # type: ignore[arg-type]

    plan = InterviewPlan()
    plan.assessment.get_topic("Python Fundamentals").consecutive_failures = 1
    dropped = planner._difficulty_for(profile, plan, 5, "Python Fundamentals")
    assert dropped == Difficulty.MEDIUM  # advanced - 1

    normal = planner._difficulty_for(profile, plan, 5, "Unrelated Topic")
    assert normal.rank > dropped.rank


def test_interview_does_not_end_before_minimums() -> None:
    """Termination is gated on 8+ questions AND 4+ days."""
    from agents.candidate_analyzer import CandidateAnalyzer
    from agents.difficulty_manager import DifficultyManager
    from agents.interview_manager import InterviewManager
    from agents.question_planner import QuestionPlanner
    from config import settings
    from memory.conversation_memory import ConversationMemory
    from models.session import InterviewSession
    from retrieval.candidate_loader import CandidateLoader

    candidates = CandidateLoader(FIXTURES_DIR)
    candidates.load()
    profile = CandidateAnalyzer().analyze(candidates.get("CAND-001"))
    curriculum = CurriculumLoader(FIXTURES_DIR)
    curriculum.load()
    retriever = CurriculumRetriever(curriculum)
    planner = QuestionPlanner(None, None, retriever, difficulty_manager=DifficultyManager())

    manager = InterviewManager.__new__(InterviewManager)
    manager._settings = settings

    def build(count: int, day_span: int) -> InterviewSession:
        session = InterviewSession(
            session_id="s-test",
            candidate_id="CAND-001",
            profile=profile,
            plan=planner.build_plan(profile),
            memory=ConversationMemory(),
        )
        for index in range(count):
            day = retriever.get_day(index % day_span)
            session.plan.questions.append(
                PlannedQuestion(
                    day_index=index % day_span,
                    day_title=day.title,
                    topic=day.primary_topic,
                    question_type=QuestionType.CONCEPTUAL,
                    difficulty=Difficulty.MEDIUM,
                    question="dummy",
                )
            )
            if index % day_span not in session.plan.days_covered:
                session.plan.days_covered.append(index % day_span)
        return session

    # 8 questions but only 2 days -> must NOT terminate.
    assert manager._should_terminate(build(8, 2)) is False
    # 8 questions across 4 days: mins met, but the soft target (10) is not
    # reached and no evidence is settled -> keep going.
    assert manager._should_terminate(build(8, 4)) is False
    # Soft target (10) reached with the minimums met -> terminate.
    assert manager._should_terminate(build(10, 4)) is True
    # 10 questions but only 2 days -> mins NOT met even at the soft target
    # -> keep going (never end on a maximum without the minimums).
    assert manager._should_terminate(build(10, 2)) is False
    # Absolute safety cap (max_questions=12) forces termination regardless.
    assert manager._should_terminate(build(12, 2)) is True


def test_claim_gets_verification_even_after_non_answer() -> None:
    """Per the interview rules "I know" is never accepted at face value: it
    always gets its one verification probe, even when the topic already saw
    a non-answer exchange — and a second claim moves on."""
    with _client() as client:
        session_id = str(uuid.uuid4())
        client.post(
            "/api/interview",
            json={"sessionId": session_id, "candidate": {"member": {"id": "CAND-001"}}},
        )
        # Non-answer -> one short simpler recovery (FOLLOW_UP).
        data = client.post(
            "/api/interview", json={"sessionId": session_id, "message": "hello"}
        ).json()
        assert data["state"] == "FOLLOW_UP"
        # First "I know" -> still gets its verification probe.
        data = client.post(
            "/api/interview", json={"sessionId": session_id, "message": "I know"}
        ).json()
        assert data["state"] == "FOLLOW_UP", data["state"]
        # Second "I know" -> insufficient evidence, moves on.
        data = client.post(
            "/api/interview", json={"sessionId": session_id, "message": "I know"}
        ).json()
        assert data["state"] == "QUESTIONING"


def test_interviews_finish_in_concise_band() -> None:
    """Completed interviews stay in the 8..12 main-question band — never
    the old 15-20 question marathons — while keeping the minimums."""
    strong = (
        "I would break the problem into clear components, choose the right "
        "data model, then design the interfaces between them. In production "
        "I would add monitoring, logging and automated tests, and I would "
        "weigh the trade-offs between a managed service and running it "
        "ourselves before deciding."
    )
    for label, answer in (
        ("strong", strong),
        ("idk", "I don't know"),
    ):
        with _client() as client:
            session_id = str(uuid.uuid4())
            data = _run_to_completion(client, session_id, answer)
            assert data["done"] is True, label
            assert len(data["_days_seen"]) >= 4, label
            mains = data["questionNumber"]
            assert 8 <= mains <= 12, f"{label}: {mains} main questions"
