"""Candidate analyzer.

Reads the *raw* candidate record from candidate.json (never mutating it) and
produces a normalised :class:`CandidateProfile` the rest of the engine can
depend on.  The analyzer is deliberately tolerant: candidate.json may hold a
flat record, nested mission/attempt objects, or any of several common field
spellings.  Anything that cannot be found simply yields a neutral default —
the interview still runs.
"""
from __future__ import annotations

from typing import Any

from models.candidate_profile import CandidateProfile, TopicSignal
from models.enums import Difficulty
from utils.logging import get_logger

logger = get_logger(__name__)

_SENIORITY_KEYWORDS: list[tuple[str, list[str]]] = [
    ("intern", ["intern"]),
    ("junior", ["junior", "jr", "fresher", "graduate"]),
    ("mid", ["mid", "associate", "software engineer", "swe", "developer"]),
    ("senior", ["senior", "sr", "lead", "principal", "staff", "architect"]),
    ("staff", ["staff", "principal", "architect"]),
]

_SENIORITY_DIFFICULTY: dict[str, Difficulty] = {
    "intern": Difficulty.EASY,
    "junior": Difficulty.EASY,
    "mid": Difficulty.MEDIUM,
    "senior": Difficulty.ADVANCED,
    "staff": Difficulty.ADVANCED,
}

_SENIORITY_CONFIDENCE: dict[str, float] = {
    "intern": 0.35,
    "junior": 0.45,
    "mid": 0.6,
    "senior": 0.75,
    "staff": 0.85,
}


class CandidateAnalyzer:
    """Derives the interview-relevant profile from a raw candidate record."""

    def analyze(self, raw: dict) -> CandidateProfile:
        candidate_id = self._first(
            raw, ("id", "candidate_id", "candidateId", "candidate", "name")
        )
        name = self._first(raw, ("name", "full_name", "candidate_name"), str, "")
        role = self._first(
            raw,
            ("role", "job_role", "jobRole", "designation", "applied_role", "position"),
            str,
            "",
        )
        experience = self._parse_experience(
            self._first(raw, ("experience", "years_of_experience", "experience_years", "total_experience"))
        )
        seniority = self._infer_seniority(
            role, str(experience), self._first(raw, ("level", "seniority", "band"), str, "")
        )
        education = self._first(raw, ("education", "degree", "qualification"), str, "")

        signals = self._extract_signals(raw)
        strong = self._strong_topics(signals, raw)
        weak = self._weak_topics(signals, raw)
        gaps = self._knowledge_gaps(signals, raw)
        confidence = self._confidence(signals, raw, seniority)

        baseline = _SENIORITY_DIFFICULTY[seniority]
        if signals:
            pass_rate = sum(s.passed for s in signals) / max(
                1, sum(s.attempts for s in signals)
            )
            if pass_rate < 0.4:
                # Low pass rate -> drop one difficulty step.
                baseline = Difficulty.from_rank(baseline.rank - 1)

        return CandidateProfile(
            candidate_id=str(candidate_id),
            name=name,
            role=role,
            experience_years=experience,
            seniority=seniority,
            education=education,
            strong_topics=strong,
            weak_topics=weak,
            knowledge_gaps=gaps,
            topic_signals=signals,
            baseline_difficulty=baseline,
            confidence=confidence,
            total_attempts=sum(s.attempts for s in signals),
            raw=raw,
        )

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _first(
        record: dict,
        keys: tuple[str, ...],
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
        text = str(value)
        import re

        match = re.search(r"(\d+(?:\.\d+)?)", text)
        return float(match.group(1)) if match else 0.0

    @classmethod
    def _infer_seniority(cls, role: str, experience: str, explicit: str) -> str:
        haystack = f"{role} {experience} {explicit}".lower()
        for level, keywords in _SENIORITY_KEYWORDS:
            if any(keyword in haystack for keyword in keywords):
                return level
        return "mid"

    def _extract_signals(self, raw: dict) -> list[TopicSignal]:
        """Walk missions / attempts / signals entries into TopicSignal list."""
        signals: dict[str, TopicSignal] = {}
        missions = self._first(raw, ("missions", "mission_history", "attempts_list", "topics_history"))
        if isinstance(missions, list):
            for mission in missions:
                if not isinstance(mission, dict):
                    continue
                topic = self._first(
                    mission, ("topic", "topic_name", "title", "name", "subject"), str, ""
                )
                if not topic:
                    continue
                signal = signals.setdefault(topic, TopicSignal(topic=topic))
                status = str(
                    self._first(
                        mission,
                        ("status", "result", "outcome", "state", "passed"),
                        str,
                        "",
                    )
                ).lower()
                attempts = int(self._first(mission, ("attempts", "attempt_count", "tries"), int, 0) or 0)
                signal.attempts += attempts or 1
                if status in {"passed", "pass", "success", "cleared", "true"}:
                    signal.passed += 1
                    if attempts <= 1:
                        signal.first_try_success = True
                elif status in {"failed", "fail", "error"}:
                    signal.failed += 1
                elif status in {"skipped", "skip", "deferred"}:
                    signal.skipped += 1

        # Flat boolean/status style: passed=[...], failed=[...], skipped=[...]
        self._add_flat_list(raw, "passed", signals, passed=True)
        self._add_flat_list(raw, "failed", signals, failed=True)
        self._add_flat_list(raw, "skipped", signals, skipped=True)

        # Explicit signals dict (topic -> signal words)
        signals_raw = raw.get("signals")
        if isinstance(signals_raw, dict):
            for topic, words in signals_raw.items():
                signal = signals.setdefault(str(topic), TopicSignal(topic=str(topic)))
                words_text = " ".join(words) if isinstance(words, list) else str(words)
                words_text = words_text.lower()
                if "pass" in words_text or "good" in words_text or "strong" in words_text:
                    signal.passed += 1
                if "fail" in words_text or "weak" in words_text or "struggl" in words_text:
                    signal.failed += 1
                if "skip" in words_text:
                    signal.skipped += 1
        return list(signals.values())

    @staticmethod
    def _add_flat_list(
        raw: dict,
        key: str,
        signals: dict[str, TopicSignal],
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
            if topic and topic.strip():
                signal = signals.setdefault(topic.strip(), TopicSignal(topic=topic.strip()))
                signal.attempts += 1
                if passed:
                    signal.passed += 1
                    signal.first_try_success = True
                elif failed:
                    signal.failed += 1
                elif skipped:
                    signal.skipped += 1

    @staticmethod
    def _strong_topics(signals: list[TopicSignal], raw: dict) -> list[str]:
        strong = [s.topic for s in signals if s.first_try_success or (s.passed > s.failed and s.passed > 0)]
        extra = raw.get("strong_topics") or raw.get("strengths")
        if isinstance(extra, list):
            strong.extend(str(item) for item in extra)
        return list(dict.fromkeys(strong))

    @staticmethod
    def _weak_topics(signals: list[TopicSignal], raw: dict) -> list[str]:
        weak = [
            s.topic for s in signals if s.failed > 0 and s.failed >= s.passed
        ]
        extra = raw.get("weak_topics") or raw.get("weaknesses")
        if isinstance(extra, list):
            weak.extend(str(item) for item in extra)
        return list(dict.fromkeys(weak))

    @staticmethod
    def _knowledge_gaps(signals: list[TopicSignal], raw: dict) -> list[str]:
        gaps = [s.topic for s in signals if s.skipped > 0]
        extra = raw.get("gaps") or raw.get("knowledge_gaps") or raw.get("missing")
        if isinstance(extra, list):
            gaps.extend(str(item) for item in extra)
        return list(dict.fromkeys(gaps))

    @classmethod
    def _confidence(cls, signals: list[TopicSignal], raw: dict, seniority: str) -> float:
        base = _SENIORITY_CONFIDENCE.get(seniority, 0.5)
        raw_confidence = raw.get("confidence")
        if isinstance(raw_confidence, (int, float)):
            return max(0.0, min(1.0, float(raw_confidence)))
        if signals:
            total = sum(s.attempts for s in signals)
            passed = sum(s.passed for s in signals)
            if total:
                rate = passed / total
                base = 0.6 * base + 0.4 * rate
        return max(0.0, min(1.0, base))
