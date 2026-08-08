"""Interview plan and planned questions.

The Question Planner produces the plan dynamically.
The plan stores the history of questions asked and the internal assessment state.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from models.enums import Difficulty, QuestionType


@dataclass
class TopicAssessment:
    """Internal assessment of a candidate's knowledge on a specific topic."""
    confidence: str = "unknown" # "low", "medium", "high", "unknown"
    consecutive_failures: int = 0
    evidence: list[str] = field(default_factory=list)


@dataclass
class AssessmentState:
    """Internal state tracking the candidate's evolving assessment."""
    topics: dict[str, TopicAssessment] = field(default_factory=dict)
    
    def get_topic(self, topic: str) -> TopicAssessment:
        if topic not in self.topics:
            self.topics[topic] = TopicAssessment()
        return self.topics[topic]


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
    """The history of questions asked and candidate assessment."""

    questions: list[PlannedQuestion] = field(default_factory=list)
    days_covered: list[int] = field(default_factory=list)
    assessment: AssessmentState = field(default_factory=AssessmentState)

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
