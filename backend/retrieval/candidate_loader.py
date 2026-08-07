"""Candidate loader.

Loads ``candidate.json`` verbatim and exposes individual candidate records.
The file may be a top-level list of candidates or an object with a
``candidates`` key; every record is kept exactly as-is (no field renaming,
no added fields).  The loader only needs a stable way to *look up* a
candidate, so it accepts several common id spellings.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from utils.errors import CandidateNotFoundError, DatasetUnavailableError
from utils.logging import get_logger

logger = get_logger(__name__)

_ID_KEYS = ("id", "candidate_id", "candidateId", "candidate", "name", "email")


def _candidate_id(record: dict, index: int) -> str:
    for key in _ID_KEYS:
        value = record.get(key)
        if value not in (None, ""):
            return str(value)
    return f"candidate-{index}"


class CandidateLoader:
    """Loads and caches candidate.json."""

    def __init__(self, data_dir: str | Path) -> None:
        self._path = Path(data_dir) / "candidate.json"
        self._records: list[dict] = []
        self._error: str | None = None

    @property
    def path(self) -> Path:
        return self._path

    @property
    def error(self) -> str | None:
        return self._error

    @property
    def is_available(self) -> bool:
        return self._error is None and bool(self._records)

    def load(self) -> list[dict]:
        """Load (or reload) the candidate dataset. Never writes to it."""
        if not self._path.exists():
            self._error = f"candidate.json not found at {self._path}"
            self._records = []
            logger.warning(self._error)
            return self._records

        try:
            with self._path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except json.JSONDecodeError as exc:
            self._error = f"candidate.json is not valid JSON: {exc}"
            self._records = []
            logger.error(self._error)
            return self._records

        records = payload if isinstance(payload, list) else payload.get("candidates", [])
        if not isinstance(records, list) or not records:
            self._error = "candidate.json contains no candidates"
            self._records = []
            logger.error(self._error)
            return self._records

        if not all(isinstance(record, dict) for record in records):
            self._error = "candidate.json records must be objects"
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
        """Lightweight descriptors for the frontend landing page."""
        return [
            {
                "id": _candidate_id(record, index),
                "name": str(record.get("name") or record.get("full_name") or ""),
                "role": str(
                    record.get("role")
                    or record.get("job_role")
                    or record.get("designation")
                    or record.get("jobRole")
                    or ""
                ),
            }
            for index, record in enumerate(self._records)
        ]

    def get(self, candidate_id: str) -> dict:
        """Return the raw candidate record or raise 404."""
        if not self.is_available:
            raise DatasetUnavailableError(self._error or "candidate.json unavailable")
        for index, record in enumerate(self._records):
            if str(_candidate_id(record, index)) == candidate_id:
                return record
        raise CandidateNotFoundError(
            f"Candidate '{candidate_id}' does not exist in candidate.json",
            detail=[summary["id"] for summary in self.summaries()],
        )
