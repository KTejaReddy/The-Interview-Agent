"""Interview state machine.

The conversation follows a strict lifecycle:

    START
      -> INTRODUCTION
      -> QUESTIONING        (ask base questions from the plan)
      -> FOLLOW_UP          (adapt to the candidate's last answer)
      -> NEXT_TOPIC         (bridge to the next curriculum day / topic)
      -> FINAL_QUESTION     (wrap-up / questions for the interviewer)
      -> EVALUATION
      -> FEEDBACK
      -> DONE

The :class:`InterviewStateMachine` validates every transition and raises
:class:`InvalidStateTransitionError` on illegal moves, keeping the flow
deterministic and testable.
"""
from __future__ import annotations

from enum import Enum

from utils.errors import InvalidStateTransitionError


class InterviewState(str, Enum):
    """Every possible state of an interview session."""

    START = "START"
    INTRODUCTION = "INTRODUCTION"
    QUESTIONING = "QUESTIONING"
    FOLLOW_UP = "FOLLOW_UP"
    NEXT_TOPIC = "NEXT_TOPIC"
    FINAL_QUESTION = "FINAL_QUESTION"
    EVALUATION = "EVALUATION"
    FEEDBACK = "FEEDBACK"
    DONE = "DONE"


#: Legal transitions.  Every state lists the states it may move into.
_TRANSITIONS: dict[InterviewState, set[InterviewState]] = {
    InterviewState.START: {InterviewState.INTRODUCTION},
    InterviewState.INTRODUCTION: {InterviewState.QUESTIONING},
    InterviewState.QUESTIONING: {
        InterviewState.FOLLOW_UP,
        InterviewState.NEXT_TOPIC,
        InterviewState.FINAL_QUESTION,
    },
    InterviewState.FOLLOW_UP: {
        InterviewState.QUESTIONING,
        InterviewState.FOLLOW_UP,  # consecutive follow-ups allowed
        InterviewState.NEXT_TOPIC,
        InterviewState.FINAL_QUESTION,
    },
    InterviewState.NEXT_TOPIC: {
        InterviewState.QUESTIONING,
        InterviewState.FINAL_QUESTION,
    },
    InterviewState.FINAL_QUESTION: {InterviewState.EVALUATION},
    InterviewState.EVALUATION: {InterviewState.FEEDBACK},
    InterviewState.FEEDBACK: {InterviewState.DONE},
    InterviewState.DONE: set(),
}

#: States in which the system (not the candidate) is expected to speak next.
#: The candidate only sends messages in these states.
CANDIDATE_TURN_STATES = {
    InterviewState.INTRODUCTION,
    InterviewState.QUESTIONING,
    InterviewState.FOLLOW_UP,
    InterviewState.NEXT_TOPIC,
    InterviewState.FINAL_QUESTION,
}


class InterviewStateMachine:
    """Encapsulates the current state and validates every transition."""

    def __init__(self, initial: InterviewState = InterviewState.START) -> None:
        self._current = initial

    @property
    def current(self) -> InterviewState:
        return self._current

    def can_transition(self, target: InterviewState) -> bool:
        return target in _TRANSITIONS.get(self._current, set())

    def transition(self, target: InterviewState) -> InterviewState:
        """Move to ``target`` or raise :class:`InvalidStateTransitionError`."""
        if not self.can_transition(target):
            raise InvalidStateTransitionError(
                f"Illegal transition {self._current.value} -> {target.value}"
            )
        previous = self._current
        self._current = target
        return previous

    def is_terminal(self) -> bool:
        return self._current == InterviewState.DONE

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<InterviewStateMachine state={self._current.value}>"
