"""In-memory interview session entity.

A session aggregates everything that must persist across API calls for the
whole conversation: the candidate profile, the plan, the conversation
memory, the state machine and the final feedback.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from models.candidate_profile import CandidateProfile
from models.enums import Difficulty
from models.interview_state import InterviewState, InterviewStateMachine
from models.plan import InterviewPlan
from schemas.llm import FeedbackResult


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class InterviewSession:
    """Stateful unit of an interview conversation."""

    session_id: str
    candidate_id: str
    profile: CandidateProfile
    state_machine: InterviewStateMachine = field(
        default_factory=InterviewStateMachine
    )
    plan: InterviewPlan = field(default_factory=InterviewPlan)
    memory: "ConversationMemory" = None  # type: ignore[assignment]
    # ^^^ memory is always set by InterviewManager.start_session() — the
    # None default here is only a Pydantic/dataclass safety net.
    # A proper default_factory is avoided because ConversationMemory needs
    # max_history_turns from config, which isn't available at class level.
    current_question_index: int = 0
    follow_ups_used: int = 0             # follow-ups for the current question
    last_question_day: int = 0
    current_question_text: str = ""      # exact text of the last asked question
    current_difficulty: Difficulty = Difficulty.MEDIUM
    feedback: FeedbackResult | None = None
    transcript: list[dict] = field(default_factory=list)  # [{role, text}]
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def touch(self) -> None:
        self.updated_at = _now()

    @property
    def state(self) -> InterviewState:
        return self.state_machine.current

    @property
    def completed(self) -> bool:
        return self.state_machine.is_terminal()

    @property
    def progress(self) -> int:
        """Number of base questions asked so far."""
        return self.current_question_index
