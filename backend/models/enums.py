"""Shared enums used across the interview engine."""
from __future__ import annotations

from enum import Enum


class Difficulty(str, Enum):
    """Progressive difficulty levels used by the question planner."""

    EASY = "easy"
    MEDIUM = "medium"
    ADVANCED = "advanced"

    @property
    def rank(self) -> int:
        return {"easy": 0, "medium": 1, "advanced": 2}[self.value]

    @classmethod
    def from_rank(cls, rank: int) -> "Difficulty":
        ranks = [cls.EASY, cls.MEDIUM, cls.ADVANCED]
        return ranks[max(0, min(rank, len(ranks) - 1))]


class QuestionType(str, Enum):
    """The mixed question styles the planner rotates through.

    The planner never repeats the same style back-to-back.
    """

    DEFINITION = "definition"
    CONCEPTUAL = "conceptual"
    SCENARIO = "scenario"
    ARCHITECTURE = "architecture"
    DEBUGGING = "debugging"
    TRADEOFFS = "tradeoffs"
    DESIGN = "design"
    PRODUCTION = "production"
    DEPLOYMENT = "deployment"
    REASONING = "reasoning"


class Verdict(str, Enum):
    """How the evaluator rates a single answer."""

    EXCELLENT = "excellent"
    GOOD = "good"
    WEAK = "weak"
    WRONG = "wrong"
    UNCLEAR = "unclear"


class FollowUpStrategy(str, Enum):
    """How the interviewer reacts to an answer."""

    DEEPER = "deeper"          # answer was good -> probe deeper
    SIMPLIFY = "simplify"      # answer was weak -> easier sub-question
    RECOVERY = "recovery"      # answer was wrong -> scaffold & recover
    NEXT_TOPIC = "next_topic"  # answer sufficient -> move on
    PROBE = "probe"            # answer unclear -> ask for clarification
