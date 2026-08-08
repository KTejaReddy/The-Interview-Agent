"""Candidate loader.

Loads ``candidates.json`` (or ``candidate.json``) verbatim and exposes
individual candidate records.  The file may be a top-level list of
candidates or an object with a ``candidates`` key; every record is kept
exactly as-is (no field renaming, no added fields).  Records typically look
like::

    {
      "member": {"id": "CAND-001", "name": "...", "jobRole": "...", ...},
      "missions": [{"day": 7, "title": "...", "passed": true, "attempts": 1}, ...],
      "signals": {"commitDays": 28, "missionsCompleted": 30, "missionsFirstTry": 20}
    }

but flat records (``{"id": ..., "name": ..., "role": ...}``) are also
accepted, so any dataset variant keeps working.  The loader never writes to
the file.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import CANDIDATE_DATASET_NAMES, find_dataset_file
from utils.errors import CandidateNotFoundError, DatasetUnavailableError
from utils.logging import get_logger

logger = get_logger(__name__)

_ID_KEYS = ("id", "candidate_id", "candidateId", "candidate", "name", "email")
_MEMBER_KEYS = ("member", "profile", "user", "person")


def _member(record: dict) -> dict:
    """Return the nested member/profile object when present."""
    for key in _MEMBER_KEYS:
        value = record.get(key)
        if isinstance(value, dict):
            return value
    return record


def _candidate_id(record: dict, index: int) -> str:
    member = _member(record)
    for source in (member, record):
        for key in _ID_KEYS:
            value = source.get(key)
            if value not in (None, ""):
                return str(value)
    return f"candidate-{index}"


def _first_text(*values: Any) -> str:
    for value in values:
        if value not in (None, ""):
            return str(value)
    return ""


class CandidateLoader:
    """Loads and caches candidates.json / candidate.json."""

    def __init__(self, data_dir: str | Path) -> None:
        self._data_dir = data_dir
        self._path: Path | None = None
        self._records: list[dict] = []
        self._error: str | None = None

    @property
    def path(self) -> Path | None:
        return self._path

    @property
    def error(self) -> str | None:
        return self._error

    @property
    def is_available(self) -> bool:
        return self._error is None and bool(self._records)

    def load(self) -> list[dict]:
        """Load (or reload) the candidate dataset. Never writes to it."""
        self._path = find_dataset_file(self._data_dir, CANDIDATE_DATASET_NAMES)
        if self._path is None:
            self._error = (
                "No candidate dataset found (expected candidates.json or "
                "candidate.json in the data directory, backend/, or the "
                "project root)."
            )
            self._records = []
            logger.warning(self._error)
            return self._records

        try:
            with self._path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except json.JSONDecodeError as exc:
            self._error = f"{self._path.name} is not valid JSON: {exc}"
            self._records = []
            logger.error(self._error)
            return self._records

        records = payload if isinstance(payload, list) else payload.get("candidates", [])
        if not isinstance(records, list) or not records:
            self._error = f"{self._path.name} contains no candidates"
            self._records = []
            logger.error(self._error)
            return self._records

        if not all(isinstance(record, dict) for record in records):
            self._error = f"{self._path.name} records must be objects"
            self._records = []
            logger.error(self._error)
            return self._records

        self._records = records
        self._error = None
        logger.info("Candidates loaded: %d from %s", len(records), self._path)
        return self._records

    def all(self) -> list[dict]:
        return list(self._records)

    def summaries(self) -> list[dict]:
        """Rich descriptors for the landing page (id, name, role, stats)."""
        summaries: list[dict] = []
        for index, record in enumerate(self._records):
            member = _member(record)
            missions = record.get("missions") or []
            passed = [m for m in missions if isinstance(m, dict) and m.get("passed") is True]
            skipped = [m for m in missions if isinstance(m, dict) and m.get("skipped") is True]
            failed = [m for m in missions if isinstance(m, dict) and m.get("passed") is False and not m.get("skipped")]
            struggles = [m for m in passed if int(m.get("attempts") or 0) >= 3]
            first_try = [m for m in passed if int(m.get("attempts") or 0) <= 1]
            summaries.append(
                {
                    "id": _candidate_id(record, index),
                    "name": _first_text(member.get("name"), record.get("name"), record.get("full_name")),
                    "role": _first_text(
                        member.get("jobRole"),
                        member.get("job_role"),
                        member.get("role"),
                        record.get("role"),
                        record.get("jobRole"),
                        record.get("designation"),
                    ),
                    "experience": member.get("yearsExperience") or member.get("years_of_experience") or record.get("experience") or 0,
                    "education": _first_text(member.get("education"), record.get("education"), record.get("degree")),
                    "missionsCompleted": len(passed),
                    "missionsFirstTry": len(first_try),
                    "struggles": len(struggles),
                    "skipped": len(skipped),
                    "failed": len(failed),
                    # Real per-candidate day arrays for the frontend timeline
                    "completedDays": sorted(int(m["day"]) for m in passed if m.get("day") is not None),
                    "skippedDays": sorted(int(m["day"]) for m in skipped if m.get("day") is not None),
                    "failedDays": sorted(int(m["day"]) for m in failed if m.get("day") is not None),
                    "completedTopics": [str(m.get("title", "")) for m in passed if m.get("title")],
                }
            )
        return summaries

    def get(self, candidate_id: str) -> dict:
        """Return the raw candidate record or raise 404."""
        if not self.is_available:
            raise DatasetUnavailableError(self._error or "candidate dataset unavailable")
        for index, record in enumerate(self._records):
            if str(_candidate_id(record, index)) == candidate_id:
                return record
        raise CandidateNotFoundError(
            f"Candidate '{candidate_id}' does not exist in the candidate dataset",
            detail=[summary["id"] for summary in self.summaries()],
        )
