"""Tests for the candidate analyzer (real dataset shape)."""
from __future__ import annotations

from agents.candidate_analyzer import CandidateAnalyzer
from models.enums import Difficulty


def _analyzer() -> CandidateAnalyzer:
    return CandidateAnalyzer()


def test_analyzes_member_wrapped_candidate() -> None:
    raw = {
        "member": {
            "id": "CAND-001",
            "name": "Alex Doe",
            "jobRole": "Junior Python Developer",
            "yearsExperience": 1.5,
            "education": "B.Sc. Computer Science",
            "status": "COMPLETED",
        },
        "missions": [
            {"day": 1, "title": "Python Fundamentals", "passed": True, "attempts": 1},
            {"day": 2, "title": "OOP Basics", "passed": True, "attempts": 4},
            {"day": 3, "title": "Algorithms", "passed": False, "attempts": 3},
            {"day": 4, "title": "Databases", "skipped": True},
        ],
        "signals": {"commitDays": 18, "missionsCompleted": 26, "missionsFirstTry": 4},
    }
    profile = _analyzer().analyze(raw)

    assert profile.candidate_id == "CAND-001"
    assert profile.name == "Alex Doe"
    assert profile.role == "Junior Python Developer"
    assert profile.experience_years == 1.5
    assert profile.seniority == "junior"
    assert profile.completed_days == [1, 2]
    # Strong: passed with <= 2 attempts.  Weak: passed but >= 3 attempts.
    assert "Python Fundamentals" in profile.strong_topics
    assert "OOP Basics" in profile.weak_topics
    assert "Python Fundamentals" not in profile.weak_topics
    # Failed missions are NOT claimed as knowledge.
    assert "Algorithms" in profile.failed_topics
    assert "Algorithms" not in profile.weak_topics
    assert "Algorithms" not in profile.strong_topics
    # Skipped missions are knowledge gaps, not demonstrated knowledge.
    assert "Databases" in profile.knowledge_gaps
    assert profile.baseline_difficulty == Difficulty.EASY
    assert 0.0 <= profile.confidence <= 1.0


def test_analyzes_senior_candidate() -> None:
    raw = {
        "member": {
            "id": "CAND-002",
            "name": "Priya Sharma",
            "jobRole": "Senior Backend Engineer",
            "yearsExperience": 7,
            "education": "M.Tech",
            "status": "COMPLETED",
        },
        "missions": [
            {"day": 1, "title": "Python Fundamentals", "passed": True, "attempts": 1},
        ],
        "signals": {"commitDays": 31, "missionsCompleted": 31, "missionsFirstTry": 29},
    }
    profile = _analyzer().analyze(raw)

    assert profile.seniority == "senior"
    assert profile.baseline_difficulty == Difficulty.ADVANCED
    assert profile.experience_years == 7.0
    assert profile.strong_topics
    assert profile.engagement_score >= 90


def test_skipped_missions_do_not_penalise_difficulty() -> None:
    """A candidate with many skips but strong passes keeps a high baseline."""
    raw = {
        "member": {"id": "CAND-003", "name": "Sam", "jobRole": "Staff Engineer", "yearsExperience": 15},
        "missions": [
            {"day": 1, "title": "Foundations", "passed": True, "attempts": 1},
            {"day": 2, "title": "Core", "passed": True, "attempts": 1},
            {"day": 3, "title": "Advanced", "skipped": True},
            {"day": 4, "title": "Ops", "skipped": True},
        ],
        "signals": {"commitDays": 29, "missionsCompleted": 29, "missionsFirstTry": 27},
    }
    profile = _analyzer().analyze(raw)
    assert profile.seniority == "staff"
    assert profile.baseline_difficulty == Difficulty.ADVANCED


def test_flat_record_still_works() -> None:
    raw = {
        "id": "candidate-x",
        "name": "Flat Person",
        "role": "Software Engineer",
        "missions": [
            {"topic": "python-loops", "status": "passed", "attempts": 1},
        ],
        "passed": ["alpha", "beta"],
        "failed": ["gamma"],
    }
    profile = _analyzer().analyze(raw)
    assert profile.candidate_id == "candidate-x"
    assert "python-loops" in profile.strong_topics
    assert "alpha" in profile.strong_topics
    assert "gamma" in profile.failed_topics


def test_empty_record_gets_neutral_defaults() -> None:
    profile = _analyzer().analyze({"id": "candidate-4"})
    assert profile.seniority == "mid"
    assert profile.baseline_difficulty == Difficulty.MEDIUM
    assert 0.0 <= profile.confidence <= 1.0
    assert profile.strong_topics == []
