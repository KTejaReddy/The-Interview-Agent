"""Candidate analyzer.

Reads the *raw* candidate record from ``candidates.json`` (never mutating
it) and produces a normalised :class:`CandidateProfile` the rest of the
engine can depend on.

The official dataset nests the identity under ``member`` and keeps mission
outcomes in ``missions`` with ``day`` / ``title`` / ``passed`` /
``attempts`` / ``skipped``::

    {
      "member": {"id": "CAND-001", "name": "...", "jobRole": "...",
                 "yearsExperience": 9, "education": "...", "status": "COMPLETED"},
      "missions": [{"day": 7, "title": "Embeddings Explained", "passed": true, "attempts": 1}, ...],
      "signals": {"commitDays": 28, "missionsCompleted": 30, "missionsFirstTry": 20}
    }

The analyzer keeps every mission as a :class:`TopicSignal` keyed by the
curriculum day number, and derives:

* ``strong_topics``   -- passed with <= 2 attempts (mastered),
* ``weak_topics``     -- passed but needed >= 3 attempts (struggled; probe later),
* ``failed_topics``   -- attempted but not passed (NOT claimed as knowledge),
* ``knowledge_gaps``  -- skipped missions (NOT demonstrated knowledge),
* ``completed_days``  -- day numbers of passed missions (the question pool),
* engagement / confidence -- from the cohort ``signals`` block.

Flat candidate records (no ``member`` wrapper) are still accepted.
"""
from __future__ import annotations

import re
from typing import Any

from agents.difficulty_manager import DifficultyManager
from models.candidate_profile import CandidateProfile, TopicSignal
from models.enums import Difficulty
from utils.logging import get_logger

logger = get_logger(__name__)

#: Ordered most-senior first so that "Senior Data Engineer" maps to
#: ``senior``, not to the generic ``engineer`` keyword in ``mid``.
_SENIORITY_KEYWORDS: list[tuple[str, list[str]]] = [
    ("staff", ["staff", "principal", "distinguished", "architect"]),
    ("senior", ["senior", "sr", "lead"]),
    ("mid", ["mid", "associate", "software engineer", "swe"]),
    ("junior", ["junior", "jr", "fresher", "graduate", "bootcamp"]),
    ("intern", ["intern"]),
]

_SENIORITY_CONFIDENCE: dict[str, float] = {
    "intern": 0.35,
    "junior": 0.45,
    "mid": 0.6,
    "senior": 0.75,
    "staff": 0.85,
}

_MEMBER_KEYS = ("member", "profile", "user", "person")
_MISSION_KEYS = ("missions", "mission_history", "attempts_list", "topics_history")


class CandidateAnalyzer:
    """Derives the interview-relevant profile from a raw candidate record."""

    def __init__(self, difficulty_manager: DifficultyManager | None = None) -> None:
        self._difficulty = difficulty_manager or DifficultyManager()

    def analyze(self, raw: dict) -> CandidateProfile:
        member = self._member_of(raw)
        candidate_id = self._first(
            member, ("id", "candidate_id", "candidateId"), default=self._first(
                raw, ("id", "candidate_id", "candidateId", "name")
            )
        )
        name = self._first(member, ("name", "full_name"), cast=str, default="")
        role = self._first(
            member,
            ("jobRole", "job_role", "role", "designation", "position"),
            cast=str,
            default="",
        )
        experience = self._parse_experience(
            self._first(member, ("yearsExperience", "years_of_experience", "experience"))
        )
        education = self._first(member, ("education", "degree", "qualification"), cast=str, default="")
        seniority = self._infer_seniority(
            role, str(experience), self._first(member, ("level", "seniority", "band"), cast=str, default="")
        )

        signals = self._extract_signals(raw)
        strong = self._strong_topics(signals, raw)
        weak = self._weak_topics(signals, raw)
        failed = self._failed_topics(signals, raw)
        gaps = self._knowledge_gaps(signals, raw)
        completed_days = sorted(s.day_number for s in signals if s.passed > 0 and s.day_number)
        engagement = self._engagement_score(raw)
        confidence = self._confidence(signals, raw, seniority, engagement)

        profile = CandidateProfile(
            candidate_id=str(candidate_id or name or "candidate"),
            name=name,
            role=role,
            experience_years=experience,
            seniority=seniority,
            education=education,
            strong_topics=strong,
            weak_topics=weak,
            failed_topics=failed,
            knowledge_gaps=gaps,
            completed_days=completed_days,
            topic_signals=signals,
            baseline_difficulty=Difficulty.MEDIUM,
            confidence=confidence,
            total_attempts=sum(s.attempts for s in signals),
            engagement_score=engagement,
            raw=raw,
        )
        profile.baseline_difficulty = self._difficulty.baseline_for(profile)
        return profile

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _member_of(record: dict) -> dict:
        for key in _MEMBER_KEYS:
            value = record.get(key)
            if isinstance(value, dict):
                return value
        return record

    @staticmethod
    def _first(
        record: dict,
        keys: tuple[str, ...],
        *,
        cast: type | None = None,
        default: Any = None,
    ) -> Any:
        for key in keys:
            value = record.get(key)
            if value is None:
                continue
            try:
                return cast(value) if cast else value
            except (TypeError, ValueError):
                continue
        return default

    @staticmethod
    def _parse_experience(value: Any) -> float:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        match = re.search(r"(\d+(?:\.\d+)?)", str(value))
        return float(match.group(1)) if match else 0.0

    @classmethod
    def _infer_seniority(cls, role: str, experience: str, explicit: str) -> str:
        haystack = f"{role} {experience} {explicit}".lower()
        for level, keywords in _SENIORITY_KEYWORDS:
            if any(keyword in haystack for keyword in keywords):
                return level
        return "mid"

    def _extract_signals(self, raw: dict) -> list[TopicSignal]:
        """Walk the missions list into TopicSignal entries keyed by day number."""
        by_day: dict[int, TopicSignal] = {}
        by_topic: dict[str, TopicSignal] = {}
        missions = self._first(raw, _MISSION_KEYS)
        if isinstance(missions, list):
            for mission in missions:
                if not isinstance(mission, dict):
                    continue
                title = str(
                    self._first(mission, ("title", "topic", "topic_name", "name", "subject"), cast=str, default="")
                )
                day_number = int(self._first(mission, ("day", "day_id", "day_number"), cast=int, default=0) or 0)
                attempts = int(self._first(mission, ("attempts", "attempt_count", "tries"), cast=int, default=0) or 0)
                status = str(
                    self._first(mission, ("status", "result", "outcome", "passed", "state"), cast=str, default="")
                ).lower()
                skipped = bool(
                    self._first(mission, ("skipped", "is_skipped"), cast=bool, default=False)
                )
                passed_flag = status in {"true", "pass", "passed", "success", "cleared"}
                failed_flag = status in {"false", "fail", "failed", "error"}

                if not title and not day_number:
                    continue

                signal = by_day.get(day_number)
                if signal is None:
                    signal = TopicSignal(topic=title, day_number=day_number)
                    by_day[day_number] = signal
                    by_topic[title] = signal
                elif title and title != signal.topic:
                    signal.topic = title

                if skipped:
                    signal.skipped += 1
                    # Skipped missions carry no attempt evidence: they must
                    # not drag down the candidate's pass rate.
                else:
                    signal.attempts += attempts or 1
                    if passed_flag:
                        signal.passed += 1
                        if (attempts or 1) <= 1:
                            signal.first_try_success = True
                    elif failed_flag:
                        signal.failed += 1

        # Flat style: passed=[...], failed=[...], skipped=[...] topic lists.
        self._add_flat_list(raw, "passed", by_topic, passed=True)
        self._add_flat_list(raw, "failed", by_topic, failed=True)
        self._add_flat_list(raw, "skipped", by_topic, skipped=True)

        # Merge both keyings: day-keyed signals win, topic-keyed extras fill in.
        combined = list(by_day.values())
        seen_topics = {signal.topic for signal in combined}
        for signal in by_topic.values():
            if signal.topic and signal.topic not in seen_topics:
                combined.append(signal)
                seen_topics.add(signal.topic)
        return combined

    @staticmethod
    def _add_flat_list(
        raw: dict,
        key: str,
        by_topic: dict[str, TopicSignal],
        *,
        passed: bool = False,
        failed: bool = False,
        skipped: bool = False,
    ) -> None:
        entries = raw.get(key)
        if not isinstance(entries, list):
            return
        for entry in entries:
            topic = str(entry) if isinstance(entry, str) else None
            if not topic or not topic.strip():
                continue
            signal = by_topic.setdefault(topic.strip(), TopicSignal(topic=topic.strip()))
            signal.attempts += 1
            if passed:
                signal.passed += 1
                signal.first_try_success = True
            elif failed:
                signal.failed += 1
            elif skipped:
                signal.skipped += 1

    def _strong_topics(self, signals: list[TopicSignal], raw: dict) -> list[str]:
        strong = [s.topic for s in signals if s.passed > 0 and s.attempts <= 2]
        extra = raw.get("strong_topics") or raw.get("strengths")
        if isinstance(extra, list):
            strong.extend(str(item) for item in extra)
        return list(dict.fromkeys(t for t in strong if t))

    def _weak_topics(self, signals: list[TopicSignal], raw: dict) -> list[str]:
        # Passed but with >= 3 attempts: completed yet struggled.
        weak = [s.topic for s in signals if s.passed > 0 and s.attempts >= 3]
        extra = raw.get("weak_topics") or raw.get("weaknesses")
        if isinstance(extra, list):
            weak.extend(str(item) for item in extra)
        return list(dict.fromkeys(t for t in weak if t))

    def _failed_topics(self, signals: list[TopicSignal], raw: dict) -> list[str]:
        failed = [s.topic for s in signals if s.failed > 0 and s.passed == 0]
        extra = raw.get("failed_topics") or raw.get("failed")
        if isinstance(extra, list):
            failed.extend(str(item) for item in extra)
        return list(dict.fromkeys(t for t in failed if t))

    def _knowledge_gaps(self, signals: list[TopicSignal], raw: dict) -> list[str]:
        gaps = [s.topic for s in signals if s.skipped > 0]
        extra = raw.get("gaps") or raw.get("knowledge_gaps") or raw.get("missing")
        if isinstance(extra, list):
            gaps.extend(str(item) for item in extra)
        return list(dict.fromkeys(t for t in gaps if t))

    @classmethod
    def _engagement_score(cls, raw: dict) -> int:
        """0..100 derived from the cohort ``signals`` block (reference-style)."""
        signals = raw.get("signals")
        if not isinstance(signals, dict):
            return 50
        commit_days = int(signals.get("commitDays") or signals.get("commit_days") or 0)
        completed = int(signals.get("missionsCompleted") or signals.get("missions_completed") or 0)
        first_try = int(signals.get("missionsFirstTry") or signals.get("missions_first_try") or 0)
        if not (commit_days or completed):
            return 50
        return max(
            0,
            min(
                100,
                round(
                    (commit_days / 31) * 40
                    + (completed / 31) * 40
                    + (first_try / max(completed, 1)) * 20
                ),
            ),
        )

    @classmethod
    def _confidence(
        cls,
        signals: list[TopicSignal],
        raw: dict,
        seniority: str,
        engagement: int,
    ) -> float:
        base = _SENIORITY_CONFIDENCE.get(seniority, 0.5)
        raw_confidence = raw.get("confidence")
        if isinstance(raw_confidence, (int, float)):
            return max(0.0, min(1.0, float(raw_confidence)))
        if signals:
            total = sum(s.attempts for s in signals)
            passed = sum(s.passed for s in signals)
            if total:
                base = 0.6 * base + 0.4 * (passed / total)
        base = 0.75 * base + 0.25 * (engagement / 100)
        return max(0.0, min(1.0, base))
