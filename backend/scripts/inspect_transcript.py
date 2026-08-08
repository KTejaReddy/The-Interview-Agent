"""Live transcript inspection for the interview-experience fixes.

Drives a mixed-performance interview (greeting -> claim -> strong -> weak ->
wrong -> IDK -> strong -> strong) through the real API and prints the
interviewer's exact wording so the transcript can be reviewed for:
conversational tone, one-question phrasing, varied acknowledgements, the
2-attempt weak-concept ladder, "I know" verification, and concise length.
"""

import os
import sys
from pathlib import Path

os.environ["LLM_MOCK_MODE"] = "true"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

ANSWERS = [
    "hello",  # greeting -> one short simpler recovery
    "I know",  # claim -> one verification
    (
        "I would structure it as separate services with clear interfaces, "
        "add monitoring and tests, and weigh managed versus self-hosted "
        "trade-offs before choosing"
    ),
    "not sure",  # weak -> simplify
    "I don't know",  # 2nd failure -> move on
    (
        "We would set up a vector database, embed each document chunk, and "
        "run a similarity search to find the most relevant passages for the "
        "prompt"
    ),
    (
        "I would weigh the cost of re-embedding everything against the "
        "benefit of fresher results, then schedule reindexing off-peak"
    ),
    "I know",  # claim -> verification
    "I know",  # 2nd claim -> move on
]

#: Generic substantive answers cycled once the scripted sequence runs out, so
#: the interview always reaches DONE and the transcript can be reviewed.
GENERIC = [
    (
        "I'd start by clarifying the failure, then check the logs and the "
        "most recent deployment, and roll back if the change is suspect"
    ),
    (
        "The key is separating concerns: retrieval quality, generation "
        "grounding, and a clear evaluation loop to catch regressions early"
    ),
    (
        "I'd weigh the trade-offs: latency, cost, and maintainability, then "
        "pick the approach that is simplest to operate in production"
    ),
]


def main() -> None:
    with TestClient(app) as client:
        data = client.post(
            "/api/interview",
            json={"candidate": {"member": {"id": "CAND-010"}}},
        ).json()
        sid = data["sessionId"]
        mains = 0
        follow_ups = 0
        day_seq: list[str] = []
        print("Q1:", data["reply"])
        index = 0
        while index < 30:
            answer = (
                ANSWERS[index] if index < len(ANSWERS)
                else GENERIC[index % len(GENERIC)]
            )
            result = client.post(
                "/api/interview",
                json={"sessionId": sid, "message": answer},
            ).json()
            state = result.get("state")
            if result.get("currentDay"):
                day_seq.append(result["currentDay"])
            if state == "FOLLOW_UP":
                follow_ups += 1
            elif state == "QUESTIONING":
                mains += 1
            print(f"  [{index + 1}] CAND: {answer[:60]}")
            print(f"     -> {state}: {result['reply'][:180]}")
            index += 1
            if result.get("done"):
                print(f"DONE. mains={mains} follow_ups={follow_ups}")
                print("day sequence:", day_seq)
                print("feedback summary:", result["feedback"]["summary"])
                print("strengths:", result["feedback"]["strengths"])
                print("gaps:", result["feedback"]["gaps"])
                return


if __name__ == "__main__":
    main()
