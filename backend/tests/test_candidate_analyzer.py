"""Tests for the candidate analyzer."""
from __future__ import annotations

from agents.candidate_analyzer import CandidateAnalyzer
from models.enums import Difficulty


def _analyzer() -> CandidateAnalyzer:
    return CandidateAnalyzer()


def test_analyzes_junior_candidate() -> None:
    raw = {
        "id": "candidate-1",
        "name": "Alex Doe",
        "role": "Junior Python Developer",
        "experience": 1.5,
        "missions": [
            {"topic": "python-loops", "status": "passed", "attempts": 1},
            {"topic": "oops-classes", "status": "failed", "attempts": 3},
            {"topic": "dsa-complexity", "status": "skipped", "attempts": 0},
        ],
        "skipped": ["algorithms"],
    }
    profile = _analyzer().analyze(raw)

    assert profile.candidate_id == "candidate-1"
    assert profile.name == "Alex Doe"
    assert profile.role == "Junior Python Developer"
    assert profile.experience_years == 1.5
    assert profile.seniority == "junior"
    assert "python-loops" in profile.strong_topics
    assert "oops-classes" in profile.weak_topics
    assert "dsa-complexity" in profile.knowledge_gaps
    assert "algorithms" in profile.knowledge_gaps
    assert profile.baseline_difficulty == Difficulty.EASY
    assert 0.0 <= profile.confidence <= 1.0


def test_analyzes_senior_candidate() -> None:
    raw = {
        "id": "candidate-2",
        "name": "Priya Sharma",
        "role": "Senior Backend Engineer",
        "experience": 7,
        "missions": [
            {"topic": "db-normalization", "status": "passed", "attempts": 1},
        ],
    }
    profile = _analyzer().analyze(raw)

    assert profile.seniority == "senior"
    assert profile.baseline_difficulty == Difficulty.ADVANCED
    assert profile.experience_years == 7.0
    assert profile.strong_topics  # first-try success


def test_handles_flat_and_signal_structures() -> None:
    raw = {
        "id": "candidate-3",
        "passed": ["alpha", "beta"],
        "failed": ["gamma"],
        "signals": {"delta": ["strong"]},
    }
    profile = _analyzer().analyze(raw)

    assert "alpha" in profile.strong_topics
    assert "gamma" in profile.weak_topics
    assert profile.total_attempts >= 3


def test_empty_record_gets_neutral_defaults() -> None:
    profile = _analyzer().analyze({"id": "candidate-4"})
    assert profile.seniority == "mid"
    assert profile.baseline_difficulty == Difficulty.MEDIUM
    assert 0.0 <= profile.confidence <= 1.0
    assert profile.strong_topics == []
