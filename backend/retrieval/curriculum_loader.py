"""Curriculum loader.

Loads ``curriculum.json`` from the data directory and exposes a normalised
view of each curriculum day (objectives, tools, module, learning goals and
topics).  The raw dataset is never modified and no curriculum content is
ever invented: whatever fields exist in the file are exposed verbatim.

The loader is deliberately tolerant of the exact JSON shape.  It accepts
either a top-level list of days or an object with a ``days`` key, and each
day may use any of the common field spellings.  Unknown structures degrade
gracefully instead of crashing, and ``is_available`` reports the failure.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from utils.logging import get_logger

logger = get_logger(__name__)

#: Field spellings accepted for the same semantic concept.
_DAY_KEYS = ("id", "day", "day_id", "index", "number")
_TITLE_KEYS = ("title", "name", "topic", "day_title")
_MODULE_KEYS = ("module", "module_name", "unit")
_OBJECTIVES_KEYS = ("objectives", "learning_objectives", "goals")
_TOOLS_KEYS = ("tools", "tooling", "technologies", "stack")
_LEARNING_KEYS = ("learning_goals", "learning_goals_list", "outcomes", "learning_outcomes")
_TOPICS_KEYS = ("topics", "subtopics", "sections", "topics_list")


@dataclass
class CurriculumDay:
    """Normalised single curriculum day (raw fields preserved in ``raw``)."""

    day_id: Any
    title: str
    module: str = ""
    objectives: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    learning_goals: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    raw: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "day_id": self.day_id,
            "title": self.title,
            "module": self.module,
            "objectives": list(self.objectives),
            "tools": list(self.tools),
            "learning_goals": list(self.learning_goals),
            "topics": list(self.topics),
        }


def _pick(record: dict, keys: tuple[str, ...]) -> Any:
    """Return the value for the first present key in ``keys``."""
    for key in keys:
        if key in record and record[key] is not None:
            return record[key]
    return None


def _as_str_list(value: Any) -> list[str]:
    """Normalise a scalar or list into a list of strings."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


class CurriculumLoader:
    """Loads and caches curriculum.json."""

    def __init__(self, data_dir: str | Path) -> None:
        self._path = Path(data_dir) / "curriculum.json"
        self._days: list[CurriculumDay] = []
        self._error: str | None = None

    @property
    def path(self) -> Path:
        return self._path

    @property
    def error(self) -> str | None:
        return self._error

    @property
    def is_available(self) -> bool:
        return self._error is None and bool(self._days)

    def load(self) -> list[CurriculumDay]:
        """Load (or reload) the curriculum. Never writes to the dataset."""
        if not self._path.exists():
            self._error = f"curriculum.json not found at {self._path}"
            self._days = []
            logger.warning(self._error)
            return self._days

        try:
            with self._path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except json.JSONDecodeError as exc:
            self._error = f"curriculum.json is not valid JSON: {exc}"
            self._days = []
            logger.error(self._error)
            return self._days

        days = payload if isinstance(payload, list) else payload.get("days", [])
        if not isinstance(days, list) or not days:
            self._error = "curriculum.json contains no curriculum days"
            self._days = []
            logger.error(self._error)
            return self._days

        self._days = [self._normalise_day(index, day) for index, day in enumerate(days)]
        self._error = None
        logger.info(
            "Curriculum loaded: %d days from %s", len(self._days), self._path
        )
        return self._days

    def _normalise_day(self, index: int, day: Any) -> CurriculumDay:
        if not isinstance(day, dict):
            day = {"title": str(day)}
        day_id = _pick(day, _DAY_KEYS)
        if day_id is None:
            day_id = index
        title = str(_pick(day, _TITLE_KEYS) or f"Day {index + 1}")
        return CurriculumDay(
            day_id=day_id,
            title=title,
            module=str(_pick(day, _MODULE_KEYS) or ""),
            objectives=_as_str_list(_pick(day, _OBJECTIVES_KEYS)),
            tools=_as_str_list(_pick(day, _TOOLS_KEYS)),
            learning_goals=_as_str_list(_pick(day, _LEARNING_KEYS)),
            topics=_as_str_list(_pick(day, _TOPICS_KEYS)),
            raw=day,
        )

    def get_day(self, index: int) -> CurriculumDay | None:
        if 0 <= index < len(self._days):
            return self._days[index]
        return None

    @property
    def days(self) -> list[CurriculumDay]:
        return list(self._days)

    @property
    def count(self) -> int:
        return len(self._days)
