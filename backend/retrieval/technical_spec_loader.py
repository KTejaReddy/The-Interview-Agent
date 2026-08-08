"""Technical spec loader.

Reads ``technical-spec.md`` from the data directory (or the project root)
and keeps its raw markdown available to the feedback generator and API
layer so the project can stay aligned with the specification document.  The
file is read only.
"""
from __future__ import annotations

from pathlib import Path

from config import SPEC_DATASET_NAMES, find_dataset_file
from utils.logging import get_logger

logger = get_logger(__name__)


class TechnicalSpecLoader:
    """Loads and caches technical-spec.md."""

    def __init__(self, data_dir: str | Path) -> None:
        self._data_dir = data_dir
        self._path: Path | None = None
        self._content: str | None = None

    @property
    def path(self) -> Path | None:
        return self._path

    @property
    def is_available(self) -> bool:
        return self._content is not None

    def load(self) -> str | None:
        """Load the spec; returns None (with a logged warning) if missing."""
        self._path = find_dataset_file(self._data_dir, SPEC_DATASET_NAMES)
        if self._path is None:
            logger.warning(
                "technical-spec.md not found in the data directory or project root"
            )
            self._content = None
            return None
        try:
            self._content = self._path.read_text(encoding="utf-8")
        except OSError as exc:  # pragma: no cover - platform edge case
            logger.error("Failed to read technical-spec.md: %s", exc)
            self._content = None
            return None
        logger.info("Technical spec loaded from %s", self._path)
        return self._content

    def content(self) -> str | None:
        return self._content
