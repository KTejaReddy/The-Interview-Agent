"""End-to-end API tests.

Runs the complete interview lifecycle through HTTP using the deterministic
mock LLM provider (no network, no API key).  Exercises the required rules:

* conversational POST /api/interview with sessionId,
* minimum question count and day coverage,
* state machine reaching DONE,
* structured feedback exposing exactly summary/strengths/gaps/next,
* graceful error handling for unknown candidates and sessions.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from main import app


def _client() -> TestClient:
    return TestClient(app)


def test_health_reports_datasets_and_mock_mode() -> None:
    with _client() as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["curriculumDays"] == 6
        assert data["candidates"] == 2
        assert data["specLoaded"] is True
        assert data["mockMode"] is True
        assert data["llmConfigured"] is True


def test_candidates_endpoint() -> None:
    with _client() as client:
        response = client.get("/api/candidates")
        assert response.status_code == 200
        candidates = response.json()
        assert len(candidates) == 2
        ids = {candidate["id"] for candidate in candidates}
        assert ids == {"candidate-1", "candidate-2"}


def test_unknown_candidate_returns_404() -> None:
    with _client() as client:
        response = client.post(
            "/api/interview",
            json={"candidateId": "ghost", "message": "Hello"},
        )
        assert response.status_code == 404
        body = response.json()
        assert body["detail"]["code"] == "candidate_not_found"


def test_blank_message_returns_400() -> None:
    with _client() as client:
        response = client.post(
            "/api/interview",
            json={"candidateId": "candidate-1", "message": "   "},
        )
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "malformed_request"


def test_unknown_session_returns_404() -> None:
    with _client() as client:
        response = client.post(
            "/api/interview",
            json={"candidateId": "candidate-1", "message": "Hi", "sessionId": "nope"},
        )
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "session_not_found"


def test_full_interview_reaches_done_with_feedback() -> None:
    with _client() as client:
        # Turn 1: start
        response = client.post(
            "/api/interview",
            json={"candidateId": "candidate-1", "message": "Hello, I'm ready"},
        )
        assert response.status_code == 200
        data = response.json()
        session_id = data["sessionId"]
        assert data["state"] == "QUESTIONING"
        assert data["totalQuestions"] >= 8
        assert data["interviewComplete"] is False

        # Turns 2..N: answer every question until complete
        days_seen: set[str] = set()
        if data["currentDay"]:
            days_seen.add(data["currentDay"])
        
        turn_count = 1
        while not data["interviewComplete"] and turn_count < 20:
            turn_count += 1
            response = client.post(
                "/api/interview",
                json={
                    "candidateId": "candidate-1",
                    "sessionId": session_id,
                    "message": (
                        "I would design it with clear responsibilities, "
                        "consider edge cases and keep the interfaces simple."
                    ),
                },
            )
            assert response.status_code == 200
            data = response.json()
            if data["currentDay"]:
                days_seen.add(data["currentDay"])
            if data["interviewComplete"]:
                break
            # Mock evaluator always moves on; we stay in QUESTIONING or hit
            # FINAL_QUESTION after the last planned question.
            assert data["state"] in {"QUESTIONING", "FINAL_QUESTION", "DONE"}

        # The final "any questions?" reply triggers feedback.
        if data["state"] == "FINAL_QUESTION":
            response = client.post(
                "/api/interview",
                json={
                    "candidateId": "candidate-1",
                    "sessionId": session_id,
                    "message": "No questions, thank you!",
                },
            )
            assert response.status_code == 200
            data = response.json()

        # --- assertions on the finished interview --------------------------
        assert data["interviewComplete"] is True
        assert data["state"] == "DONE"
        assert len(days_seen) >= 4, f"Only {len(days_seen)} days covered"

        feedback = data["feedback"]
        assert feedback is not None
        # Exactly the fields required by the specification.
        assert set(feedback.keys()) == {"summary", "strengths", "gaps", "next"}
        assert feedback["summary"]
        assert isinstance(feedback["strengths"], list) and feedback["strengths"]
        assert isinstance(feedback["gaps"], list) and feedback["gaps"]
        assert isinstance(feedback["next"], list) and feedback["next"]
        # Internal fields must NOT be exposed.
        assert "score" not in feedback
        assert "confidence" not in feedback
        assert "topics_covered" not in feedback

        # Resume endpoint returns the finished state.
        resume = client.get(f"/api/interview/{session_id}")
        assert resume.status_code == 200
        snapshot = resume.json()
        assert snapshot["state"] == "DONE"
        assert snapshot["interviewComplete"] is True
        assert snapshot["feedback"]["summary"]


def test_resume_returns_transcript() -> None:
    with _client() as client:
        started = client.post(
            "/api/interview",
            json={"candidateId": "candidate-2", "message": "Hi there"},
        ).json()
        snapshot = client.get(f"/api/interview/{started['sessionId']}")
        assert snapshot.status_code == 200
        body = snapshot.json()
        # The candidate message plus the interviewer's introduction reply.
        assert len(body["messages"]) == 2
        assert body["messages"][0]["role"] == "candidate"
        assert body["messages"][1]["role"] == "interviewer"
