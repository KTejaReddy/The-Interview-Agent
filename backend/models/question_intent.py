"""Question intent.

Separates *what we want to assess* from *how the interviewer phrases it*.
The planner constructs a :class:`QuestionIntent` deterministically (from the
candidate profile, the curriculum and the conversation so far), and the LLM
only translates that intent into natural interviewer language.

This is the opposite of the old flow::

    topic title -> question template -> question text

because the intent pins down the exact curriculum objective, the derived
technical concept and the evidence bar before any text is generated.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class QuestionIntent:
    """Structured description of what the next question must assess."""

    curriculum_day: int            # the curriculum's own day number (e.g. 7)
    topic: str                     # day title (a label, never the question)
    module: str                    # module the day belongs to
    learning_objective: str        # the exact objective being assessed
    concept: str                   # technical concept derived from the objective
    cognitive_level: str           # ladder label, e.g. "Level 3 — application"
    purpose: str                   # what we want to learn about the candidate
    expected_evidence: list[str] = field(default_factory=list)  # evidence bar
    difficulty: str = "medium"     # target difficulty
    relationship: str = ""         # how this connects to the previous topic
    candidate_signal: str = ""     # which profile signal drove this choice

    def to_dict(self) -> dict:
        return {
            "curriculum_day": self.curriculum_day,
            "topic": self.topic,
            "module": self.module,
            "learning_objective": self.learning_objective,
            "concept": self.concept,
            "cognitive_level": self.cognitive_level,
            "purpose": self.purpose,
            "expected_evidence": list(self.expected_evidence),
            "difficulty": self.difficulty,
            "relationship": self.relationship,
            "candidate_signal": self.candidate_signal,
        }
