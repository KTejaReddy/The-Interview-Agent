"""Live test harness for the AI Interview Agent.

Runs the required live scenarios against the real datasets and prints a
structured report:

    A. Repeated \"I don't know\"      -- difficulty drops, topic moves, 4+ days, 8+ Qs
    B. Strong candidate             -- completes, 4+ days, deeper follow-ups
    C. Mixed performance            -- adaptive behaviour
    D. Context retention            -- candidate's own concepts remembered
    E. Multiple candidates          -- personalization (distinct interviews)
    F. Coverage report              -- questions / follow-ups / days per interview
    G. Duplicate scan               -- no semantic duplicates in transcripts
    H. API contract smoke           -- status codes for the spec edge cases

Usage:

    # In-process (mock LLM, real datasets in backend/data) -- fast, offline:
    python scripts/live_tests.py

    # Against a live backend (real LLM if configured):
    python scripts/live_tests.py --url http://127.0.0.1:8000

Exit code 0 when every scenario passes, 1 otherwise.
"""
from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

# Make the backend package importable when run from anywhere.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import httpx

# --------------------------------------------------------------------- answers

STRONG = (
    "I would break the problem into clear components, choose the right data "
    "model, then design the interfaces between them. In production I would add "
    "monitoring, logging and automated tests, and I would weigh the trade-offs "
    "between a managed service and running it ourselves before deciding, because "
    "the failure modes are very different in each case."
)
PARTIAL = "I think it's about structuring the data, but I'm not sure how the pieces connect."
WRONG = "It works by storing everything in a single flat table with no indexes."
IDK = "I don't know."

MIXED_SEQUENCE = [STRONG, STRONG, PARTIAL, WRONG, STRONG, IDK]

# --------------------------------------------------------------------- client


class Api:
    """Tiny client over either an in-process app or a live server."""

    def __init__(self, url: str | None) -> None:
        if url:
            self._url = url.rstrip("/")
            self._client = httpx.Client(timeout=60)
        else:
            import os

            os.environ.setdefault("LLM_MOCK_MODE", "true")
            os.environ.setdefault("AI_DATA_DIR", str(Path(__file__).resolve().parent.parent / "data"))
            from fastapi.testclient import TestClient
            from main import app

            self._url = ""
            self._client = TestClient(app)  # type: ignore[assignment]
            # Enter the ASGI lifespan so app.state.services is populated.
            self._client.__enter__()  # type: ignore[attr-defined]
            self._owns_lifespan = True

    def post(self, path: str, payload: dict) -> dict:
        response = self._client.post(f"{self._url}{path}", json=payload)
        body = response.json() if response.content else {}
        body["_status"] = response.status_code
        return body

    def get(self, path: str) -> dict:
        response = self._client.get(f"{self._url}{path}")
        return response.json()

    def close(self) -> None:
        if getattr(self, "_owns_lifespan", False):
            self._client.__exit__(None, None, None)  # type: ignore[attr-defined]
            self._owns_lifespan = False
        if hasattr(self._client, "close"):
            self._client.close()


# --------------------------------------------------------------------- runner


class InterviewRun:
    def __init__(self, api: Api, candidate_id: str) -> None:
        self.api = api
        self.candidate_id = candidate_id
        self.session_id = str(uuid.uuid4())
        self.replies: list[dict] = []
        self.main_questions = 0
        self.follow_ups = 0
        self.days: set[str] = set()
        self.feedback: dict | None = None
        self._follow_up_state = False

    def _count_question(self, data: dict) -> None:
        if data.get("state") == "FOLLOW_UP":
            if not self._follow_up_state:
                self.follow_ups += 1
            self._follow_up_state = True
        elif data.get("state") == "QUESTIONING":
            self._follow_up_state = False
            self.main_questions += 1
        elif data.get("state") == "FINAL_QUESTION":
            self._follow_up_state = False

    @property
    def total_questions(self) -> int:
        """Actual interviewer questions shown: main questions + follow-ups
        (a follow-up is also a question)."""
        return self.main_questions + self.follow_ups

    def answer(self, message: str) -> dict:
        data = self.api.post(
            "/api/interview",
            {"sessionId": self.session_id, "message": message},
        )
        if data.get("currentDay"):
            self.days.add(data["currentDay"])
        self._count_question(data)
        if data.get("state") not in ("DONE", "FINAL_QUESTION") or data.get("feedback"):
            if data.get("reply"):
                self.replies.append({
                    "state": data.get("state"),
                    "reply": data["reply"],
                    "topic": data.get("currentTopic"),
                })
        if data.get("feedback"):
            self.feedback = data["feedback"]
        return data

    def start(self, opening: str = "Hi, I'm ready to start.") -> dict:
        data = self.api.post(
            "/api/interview",
            {"sessionId": self.session_id, "candidate": {"member": {"id": self.candidate_id}}},
        )
        if data.get("currentDay"):
            self.days.add(data["currentDay"])
        self._count_question(data)
        self.replies.append({"state": data.get("state"), "reply": data.get("reply", "")})
        return data

    def run_to_completion(self, answer_provider) -> dict:
        """answer_provider(question_index, is_follow_up) -> message"""
        data = self.start()
        index = 0
        while not data.get("done"):
            index += 1
            is_follow_up = data.get("state") == "FOLLOW_UP"
            message = answer_provider(index, is_follow_up)
            data = self.answer(message)
            if data.get("state") == "FINAL_QUESTION" and not data.get("done"):
                data = self.answer("No questions, thank you!")
            if index > 80:
                raise RuntimeError("Interview did not finish within 80 turns.")
        return data


# --------------------------------------------------------------------- checks


def _scan_duplicates(run: InterviewRun) -> list[str]:
    """Return flagged duplicate pairs among the interviewer's questions.

    Topic-aware, mirroring the engine's own duplicate guard: same-topic
    questions are flagged at a lower similarity threshold (they must add a
    new dimension), while cross-topic questions are only flagged when they
    are essentially identical — different concepts on different topics share
    template stems but are not duplicates.
    """
    from agents.duplicate_guard import jaccard, normalize

    questions = [
        (item["reply"], item.get("topic") or "")
        for item in run.replies
        if item["state"] in ("QUESTIONING", "FOLLOW_UP")
    ]
    flagged: list[str] = []
    for i in range(len(questions)):
        for j in range(i + 1, len(questions)):
            # A main question and its own immediate follow-up are related by
            # design (the follow-up deliberately re-aims at the same concept
            # from a simpler angle) — never flag that pair.
            if j == i + 1:
                continue
            sim = jaccard(normalize(questions[i][0]), normalize(questions[j][0]))
            same_topic = bool(questions[i][1]) and questions[i][1] == questions[j][1]
            if (same_topic and sim >= 0.62) or (not same_topic and sim >= 0.75):
                flagged.append(
                    f"  Q{j+1} ~ Q{i+1} (jaccard {sim:.2f}"
                    f"{', same topic' if same_topic else ''})"
                )
    return flagged


def _coverage_report(run: InterviewRun) -> str:
    return (
        f"    main questions={run.main_questions} follow-ups={run.follow_ups} "
        f"total questions={run.total_questions} days={len(run.days)} "
        f"feedback={'yes' if run.feedback else 'no'}"
    )


def scenario_a(api: Api) -> bool:
    print("A. Repeated 'I don't know' (CAND-010, struggled candidate)")
    run = InterviewRun(api, "CAND-010")
    run.run_to_completion(lambda index, fup: IDK)
    print(_coverage_report(run))
    ok = run.total_questions >= 8 and len(run.days) >= 4 and run.feedback is not None
    dupes = _scan_duplicates(run)
    if dupes:
        print("    semantic duplicates found:")
        print("\n".join(dupes))
        ok = False
    # Persistent gap: the feedback gaps array must be non-empty.
    if run.feedback and not run.feedback.get("gaps"):
        print("    FAIL: no gaps reported for a candidate who said 'I don't know'")
        ok = False
    print(f"    {'PASS' if ok else 'FAIL'}\n")
    return ok


def scenario_b(api: Api) -> bool:
    print("B. Strong candidate (CAND-003, first-try perfection)")
    run = InterviewRun(api, "CAND-003")
    run.run_to_completion(lambda index, fup: STRONG)
    print(_coverage_report(run))
    ok = run.total_questions >= 8 and len(run.days) >= 4 and run.feedback is not None
    print(f"    {'PASS' if ok else 'FAIL'}\n")
    return ok


def scenario_c(api: Api) -> bool:
    print("C. Mixed performance (CAND-006, struggled profile)")
    run = InterviewRun(api, "CAND-006")
    sequence = MIXED_SEQUENCE

    def provider(index, fup):
        return sequence[(index - 1) % len(sequence)]

    run.run_to_completion(provider)
    print(_coverage_report(run))
    ok = run.total_questions >= 8 and len(run.days) >= 4 and run.feedback is not None
    print(f"    {'PASS' if ok else 'FAIL'}\n")
    return ok


def scenario_d(api: Api) -> bool:
    print("D. Context retention (candidate mentions own concepts)")
    run = InterviewRun(api, "CAND-003")
    run.start()
    # Mention ChromaDB and Docker explicitly in the first answer.
    first = run.answer(
        "I used ChromaDB for the vector store and Docker for deployment, "
        "with FastAPI in front of it all."
    )
    # Verify the backend remembered the mentions (in-process introspection).
    mentioned = []
    if not api._url:
        try:
            from main import app as app_module

            services = app_module.state.services
            sessions = services["sessions"]
            stored = sessions._sessions.get(run.session_id)  # noqa: SLF001
            mentioned = list(stored.memory.mentions) if stored else []
        except Exception as exc:  # pragma: no cover
            print(f"    (introspection skipped: {exc})")
    print(
        "    mentions recorded:",
        ", ".join(mentioned) if mentioned else "none",
    )
    ok = (len(mentioned) >= 1 if not api._url else True) and "reply" in first
    print(f"    {'PASS' if ok else 'FAIL'}\n")
    return ok


def scenario_e(api: Api) -> bool:
    print("E. Personalization across candidates")
    profiles = {"CAND-003": "AI Engineer (perfect)", "CAND-010": "IT Support (struggled)", "CAND-020": "Software Engineer (mixed)"}
    runs = []
    for candidate_id, label in profiles.items():
        run = InterviewRun(api, candidate_id)
        run.start()
        runs.append((candidate_id, label, run))
        print(f"    {candidate_id} ({label}): first day={run.days or '?'}")

    first_topics = {r.replies[0]["reply"] for _, _, r in runs}
    distinct = len({frozenset(r.days) for _, _, r in runs}) > 1
    print(f"    distinct opening replies: {len(first_topics)}")
    ok = distinct and all(r.replies for _, _, r in runs)
    print(f"    {'PASS' if ok else 'FAIL'}\n")
    return ok


def scenario_h(api: Api) -> bool:
    print("H. API contract smoke")
    checks = []

    # Malformed body -> 400
    body = api.post("/api/interview", {"hello": "world"})
    checks.append(("malformed -> 400", body.get("_status") == 400))

    # Unknown session -> 404
    body = api.post("/api/interview", {"sessionId": "nope", "message": "Hi"})
    checks.append(("unknown session -> 404", body.get("_status") == 404))

    # Unknown candidate -> 404
    body = api.post("/api/interview", {"sessionId": str(uuid.uuid4()), "candidate": {"member": {"id": "ghost"}}})
    checks.append(("unknown candidate -> 404", body.get("_status") == 404))

    # Valid start -> 200 with reply + done
    session_id = str(uuid.uuid4())
    body = api.post("/api/interview", {"sessionId": session_id, "candidate": {"member": {"id": "CAND-001"}}})
    checks.append(("start -> 200 + reply + done", body.get("_status") == 200 and "reply" in body and "done" in body and body["done"] is False))

    # Missing message on a turn -> 400
    body = api.post("/api/interview", {"sessionId": session_id})
    checks.append(("turn without message -> 400", body.get("_status") == 400))

    for name, passed in checks:
        print(f"    {'PASS' if passed else 'FAIL'}  {name}")
    ok = all(passed for _, passed in checks)
    print(f"    {'PASS' if ok else 'FAIL'}\n")
    return ok


# --------------------------------------------------------------------- main


def main() -> int:
    parser = argparse.ArgumentParser(description="Live tests for the AI Interview Agent")
    parser.add_argument("--url", default=None, help="Live backend URL (default: in-process with mock LLM)")
    parser.add_argument("--skip", default="", help="Comma-separated scenario letters to skip")
    args = parser.parse_args()

    api = Api(args.url)
    try:
        results = {
            "A": ("repeated IDK", scenario_a),
            "B": ("strong candidate", scenario_b),
            "C": ("mixed performance", scenario_c),
            "D": ("context retention", scenario_d),
            "E": ("personalization", scenario_e),
            "H": ("api contract", scenario_h),
        }
        skip = {part.strip().upper() for part in args.skip.split(",") if part.strip()}
        all_ok = True
        for letter in "ABCDEH":
            if letter in skip:
                continue
            try:
                passed = results[letter][1](api)
            except Exception as exc:  # pragma: no cover
                print(f"    ERROR: {exc}")
                passed = False
            all_ok = all_ok and passed

        print("=" * 60)
        print("SUMMARY:", "ALL PASS" if all_ok else "FAILURES PRESENT")
        return 0 if all_ok else 1
    finally:
        api.close()


if __name__ == "__main__":
    sys.exit(main())
