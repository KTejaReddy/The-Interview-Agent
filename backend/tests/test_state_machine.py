"""Tests for the interview state machine."""
from __future__ import annotations

import pytest

from models.interview_state import InterviewState, InterviewStateMachine
from utils.errors import InvalidStateTransitionError


def test_starts_in_start_state() -> None:
    machine = InterviewStateMachine()
    assert machine.current == InterviewState.START


def test_happy_path_reaches_done() -> None:
    machine = InterviewStateMachine()
    path = [
        InterviewState.INTRODUCTION,
        InterviewState.QUESTIONING,
        InterviewState.FOLLOW_UP,
        InterviewState.QUESTIONING,
        InterviewState.NEXT_TOPIC,
        InterviewState.QUESTIONING,
        InterviewState.FINAL_QUESTION,
        InterviewState.EVALUATION,
        InterviewState.FEEDBACK,
        InterviewState.DONE,
    ]
    for state in path:
        assert machine.can_transition(state)
        machine.transition(state)
    assert machine.is_terminal()
    assert machine.current == InterviewState.DONE


def test_consecutive_follow_ups_allowed() -> None:
    machine = InterviewStateMachine(InterviewState.FOLLOW_UP)
    assert machine.can_transition(InterviewState.FOLLOW_UP)
    machine.transition(InterviewState.FOLLOW_UP)
    assert machine.current == InterviewState.FOLLOW_UP


def test_illegal_transition_raises() -> None:
    machine = InterviewStateMachine()
    with pytest.raises(InvalidStateTransitionError):
        machine.transition(InterviewState.DONE)


def test_done_is_terminal() -> None:
    machine = InterviewStateMachine(InterviewState.DONE)
    assert machine.is_terminal()
    assert not machine.can_transition(InterviewState.START)
