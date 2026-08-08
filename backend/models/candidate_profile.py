"""Candidate profile produced by the Candidate Analyzer.

This is a *derived* view of the raw candidate record inside
``candidates.json``.  The raw dataset is never mutated; the analyzer only
reads it and produces a normalised profile the rest of the engine can rely
on regardless of how the raw file is structured.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from models.enums import Difficulty


@dataclass
class TopicSignal:
    """Normalised signal for a single curriculum day the candidate touched."""

    topic: str                  # curriculum day title (matches curriculum.json)
    day_number: int = 0         # curriculum day number (e.g. 7)
    attempts: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    first_try_success: bool = False


@dataclass
class CandidateProfile:
    """Normalised, analysis-ready candidate profile."""

    candidate_id: str
    name: str = ""
    role: str = ""
    experience_years: float = 0.0
    seniority: str = "mid"          # intern | junior | mid | senior | staff
    education: str = ""
    strong_topics: list[str] = field(default_factory=list)
    weak_topics: list[str] = field(default_factory=list)
    failed_topics: list[str] = field(default_factory=list)
    knowledge_gaps: list[str] = field(default_factory=list)
    completed_days: list[int] = field(default_factory=list)   # passed day numbers
    topic_signals: list[TopicSignal] = field(default_factory=list)
    baseline_difficulty: Difficulty = Difficulty.MEDIUM
    confidence: float = 0.5          # 0..1 estimated answer confidence
    total_attempts: int = 0
    engagement_score: int = 50       # 0..100 derived from cohort signals
    raw: dict = field(default_factory=dict)   # reference to original record

    @property
    def summary(self) -> str:
        """One-line human summary used in prompts."""
        return (
            f"{self.name or self.candidate_id} | role={self.role or 'unknown'} | "
            f"seniority={self.seniority} | experience={self.experience_years}y | "
            f"engagement={self.engagement_score}/100 | confidence={self.confidence:.2f}"
        )

    @property
    def is_completed_day(self, day_number: int) -> bool:
        return day_number in self.completed_days
