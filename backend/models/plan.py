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
    confidence: str = "unknown"  # "low", "medium", "high", "unknown"
    consecutive_failures: int = 0
    bare_claims: int = 0          # "I know"-style answers without evidence
    questions_asked: int = 0      # main questions on this topic
    follow_ups: int = 0           # follow-ups on this topic
    best_score: int = 0           # best answer score (0..10)
    worst_score: int = 10         # worst answer score (0..10)
    evidence: list[str] = field(default_factory=list)

    @property
    def saturated(self) -> bool:
        """Enough evidence has been collected on this topic."""
        return self.questions_asked + self.follow_ups >= 3

    @property
    def assessed(self) -> bool:
        return self.confidence != "unknown"

    @property
    def touched(self) -> bool:
        """True when the interviewer asked about this topic at all (even if
        the candidate produced no evidence).  Feedback must include every
        touched topic — never silently drop one."""
        return self.questions_asked > 0 or bool(self.evidence)

    @property
    def knowledge_status(self) -> str:
        """Evidence-derived knowledge status (never profile-derived).

        * ``demonstrated``        -- solid scores, no persistent failures,
        * ``partially_demonstrated`` -- mixed evidence,
        * ``incorrect``           -- wrong answers dominate,
        * ``insufficient_evidence`` -- bare claims or a single weak answer,
        * ``unknown``             -- nothing but "I don't know".
        """
        if self.confidence == "high" and self.best_score >= 7 and not self.consecutive_failures:
            return "demonstrated"
        if self.consecutive_failures >= 2:
            return "incorrect"
        if self.consecutive_failures >= 1 or self.confidence == "medium":
            if self.best_score >= 6:
                return "partially_demonstrated"
            return "insufficient_evidence"
        if self.bare_claims >= 1:
            return "insufficient_evidence"
        if self.confidence == "low":
            return "insufficient_evidence"
        return "unknown"


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
    """A single planned (base) question.

    ``question`` is the final interviewer wording; ``learning_objective`` /
    ``concept`` / ``expected_evidence`` are the structured intent that
    question is grounded in (the curriculum's own wording, never invented).
    """

    day_index: int              # 0-based index into the curriculum days
    day_title: str
    topic: str
    question_type: QuestionType
    difficulty: Difficulty
    question: str               # full interviewer question text
    intent: str = ""            # purpose the question tries to establish
    learning_objective: str = ""  # exact objective being assessed
    concept: str = ""             # technical concept derived from the objective
    expected_evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "day_index": self.day_index,
            "day_title": self.day_title,
            "topic": self.topic,
            "question_type": self.question_type.value,
            "difficulty": self.difficulty.value,
            "question": self.question,
            "intent": self.intent,
            "learning_objective": self.learning_objective,
            "concept": self.concept,
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
