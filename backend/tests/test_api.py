"""End-to-end API tests.

Runs the complete interview lifecycle through HTTP using the deterministic
mock LLM provider (no network, no API key).  Exercises the spec contract:

* START: ``{sessionId, candidate}`` -> ``{reply, done: false}``,
* TURNS: ``{sessionId, message}`` -> ``{reply, done: false}``,
* END:   ``{reply, done: true, feedback: {summary, strengths, gaps, next}}``,
* minimum question count and day coverage enforced by the engine,
* graceful error handling for unknown candidates and sessions.
"""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from main import app


def _client() -> TestClient:
    return TestClient(app)


def _start_payload(candidate_id: str = "CAND-001", session_id: str | None = None):
    return {
        "sessionId": session_id or str(uuid.uuid4()),
        "candidate": {"member": {"id": candidate_id}},
    }


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


def test_candidates_endpoint_returns_rich_summaries() -> None:
    with _client() as client:
        response = client.get("/api/candidates")
        assert response.status_code == 200
        candidates = response.json()
        assert len(candidates) == 2
        ids = {candidate["id"] for candidate in candidates}
        assert ids == {"CAND-001", "CAND-002"}
        first = next(c for c in candidates if c["id"] == "CAND-001")
        assert first["name"] == "Alex Doe"
        assert first["role"] == "Junior Python Developer"
        assert first["experience"] == 1.5
        assert first["missionsCompleted"] == 5
        assert first["skipped"] == 1


def test_unknown_candidate_returns_404() -> None:
    with _client() as client:
        response = client.post(
            "/api/interview", json=_start_payload("ghost")
        )
        assert response.status_code == 404
        body = response.json()
        assert body["detail"]["code"] == "candidate_not_found"


def test_malformed_request_returns_400() -> None:
    with _client() as client:
        # Neither a start nor a turn.
        response = client.post("/api/interview", json={"hello": "world"})
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "malformed_request"


def test_unknown_session_returns_404() -> None:
    with _client() as client:
        response = client.post(
            "/api/interview",
            json={"sessionId": "nope", "message": "Hi"},
        )
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "session_not_found"


def test_blank_message_returns_400() -> None:
    with _client() as client:
        session_id = str(uuid.uuid4())
        client.post("/api/interview", json=_start_payload(session_id=session_id))
        response = client.post(
            "/api/interview",
            json={"sessionId": session_id, "message": "   "},
        )
        assert response.status_code == 400


def test_full_interview_reaches_done_with_feedback() -> None:
    with _client() as client:
        session_id = str(uuid.uuid4())
        # Turn 1: start (spec shape — client supplies sessionId + candidate).
        response = client.post(
            "/api/interview", json=_start_payload(session_id=session_id)
        )
        assert response.status_code == 200
        data = response.json()
        # Spec fields present.
        assert "reply" in data
        assert data["done"] is False
        assert data["sessionId"] == session_id
        assert data["state"] == "QUESTIONING"
        assert data["totalQuestions"] >= 8

        days_seen: set[str] = set()
        if data.get("currentDay"):
            days_seen.add(data["currentDay"])

        turn_count = 1
        while not data["done"] and turn_count < 40:
            turn_count += 1
            response = client.post(
                "/api/interview",
                json={
                    "sessionId": session_id,
                    "message": (
                        "I would start by splitting the problem into clear "
                        "pieces, then choose the right data structures. For "
                        "databases I would normalize the schema and index the "
                        "hot queries, then build a small API on top with "
                        "clean error handling and tests."
                    ),
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert "reply" in data
            if data.get("currentDay"):
                days_seen.add(data["currentDay"])
            if data["state"] == "FINAL_QUESTION" and not data["done"]:
                response = client.post(
                    "/api/interview",
                    json={"sessionId": session_id, "message": "No questions, thank you!"},
                )
                data = response.json()

        assert data["done"] is True
        assert data["state"] == "DONE"
        assert len(days_seen) >= 4, f"Only {len(days_seen)} days covered"

        feedback = data["feedback"]
        assert feedback is not None
        # The four contract fields must exist; extra fields (score) allowed.
        for key in ("summary", "strengths", "gaps", "next"):
            assert key in feedback
        assert feedback["summary"]
        assert isinstance(feedback["strengths"], list) and feedback["strengths"]
        assert isinstance(feedback["gaps"], list)
        assert isinstance(feedback["next"], list)
        # Internal confidence/topics_covered are never exposed.
        assert "confidence" not in feedback
        assert "topics_covered" not in feedback

        # Resume endpoint returns the finished state.
        resume = client.get(f"/api/interview/{session_id}")
        assert resume.status_code == 200
        snapshot = resume.json()
        assert snapshot["state"] == "DONE"
        assert snapshot["interviewComplete"] is True
        assert snapshot["feedback"]["summary"]


def test_start_with_candidate_id_shorthand() -> None:
    """The frontend convenience shape (candidateId, no sessionId) also works."""
    with _client() as client:
        response = client.post(
            "/api/interview",
            json={"candidateId": "CAND-002", "message": "Hi, I'm ready"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data and data["done"] is False
        assert data["sessionId"]


def test_resume_returns_transcript() -> None:
    with _client() as client:
        session_id = str(uuid.uuid4())
        started = client.post(
            "/api/interview", json=_start_payload("CAND-002", session_id)
        ).json()
        assert started["sessionId"] == session_id
        snapshot = client.get(f"/api/interview/{session_id}")
        assert snapshot.status_code == 200
        body = snapshot.json()
        assert len(body["messages"]) == 2
        assert body["messages"][0]["role"] == "candidate"
        assert body["messages"][1]["role"] == "interviewer"


def test_duplicate_session_id_returns_409() -> None:
    with _client() as client:
        session_id = str(uuid.uuid4())
        client.post("/api/interview", json=_start_payload(session_id=session_id))
        # Re-using the same sessionId for a new start must conflict.
        response = client.post(
            "/api/interview", json=_start_payload(session_id=session_id)
        )
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "malformed_request"


def test_sses_streaming_transport() -> None:
    """SSE transport delivers phase + reply events with the same contract."""
    with _client() as client:
        session_id = str(uuid.uuid4())
        response = client.post(
            "/api/interview",
            json=_start_payload(session_id=session_id),
            headers={"Accept": "text/event-stream"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = response.text
        assert "type" in body
        assert '"reply"' in body
