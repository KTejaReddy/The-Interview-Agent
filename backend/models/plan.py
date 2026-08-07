"""Interview plan and planned questions.

The Question Planner produces the full plan before any question is asked:
at least ``min_questions`` questions spread across at least ``min_days``
curriculum days, with progressively increasing difficulty and a rotating
set of question styles.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from models.enums import Difficulty, QuestionType


@dataclass
class PlannedQuestion:
    """A single planned (base) question."""

    day_index: int              # 0-based index into the curriculum days
    day_title: str
    topic: str
    question_type: QuestionType
    difficulty: Difficulty
    question: str               # full interviewer question text
    intent: str = ""            # what the question tries to establish

    def to_dict(self) -> dict:
        return {
            "day_index": self.day_index,
            "day_title": self.day_title,
            "topic": self.topic,
            "question_type": self.question_type.value,
            "difficulty": self.difficulty.value,
            "question": self.question,
            "intent": self.intent,
        }


@dataclass
class InterviewPlan:
    """The complete ordered question plan for a session."""

    questions: list[PlannedQuestion] = field(default_factory=list)
    days_covered: list[int] = field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.questions)

    @property
    def distinct_days(self) -> int:
        return len(set(self.days_covered))

    def question_at(self, index: int) -> PlannedQuestion | None:
        if 0 <= index < len(self.questions):
            return self.questions[index]
        return None
