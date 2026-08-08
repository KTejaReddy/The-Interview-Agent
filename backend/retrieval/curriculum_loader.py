"""Curriculum loader.

Loads ``curriculum.json`` verbatim and exposes a normalised view of each
curriculum day (day number, module, objectives, tools and derived topics).
The raw dataset is never modified and no curriculum content is ever
invented: the ``module`` field is enriched from the file's own ``modules``
section, and when a day has no explicit ``topics`` list the day *title*
becomes the primary topic (the title is the curriculum's own wording, so
this is indexing, not hallucination).

The official dataset looks like::

    {
      "cohort": "...",
      "modules": [{"n": 3, "title": "Embeddings & Vector Search", "days": [7, 10]}, ...],
      "days": [
        {"day": 7, "title": "Embeddings Explained", "type": "AI_CORE",
         "tools": [...], "objectives": [...]}, ...
      ]
    }

The loader is tolerant of other shapes too (flat lists, ``topics`` keys,
different field spellings) and degrades gracefully.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from config import CURRICULUM_DATASET_NAMES, find_dataset_file
from utils.logging import get_logger

logger = get_logger(__name__)

#: Field spellings accepted for the same semantic concept.
_DAY_KEYS = ("day", "id", "day_id", "index", "number")
_TITLE_KEYS = ("title", "name", "day_title")
_MODULE_KEYS = ("module", "module_name", "unit")
_OBJECTIVES_KEYS = ("objectives", "learning_objectives", "goals")
_TOOLS_KEYS = ("tools", "tooling", "technologies", "stack")
_LEARNING_KEYS = ("learning_goals", "learning_goals_list", "outcomes", "learning_outcomes")
_TOPICS_KEYS = ("topics", "subtopics", "sections", "topics_list")


@dataclass
class CurriculumModule:
    """A curriculum module (from the file's ``modules`` section)."""

    number: int
    title: str
    day_start: int
    day_end: int


@dataclass
class CurriculumDay:
    """Normalised single curriculum day (raw fields preserved in ``raw``)."""

    day_number: int          # the curriculum's own day number (1..N)
    title: str
    module: str = ""
    module_number: int = 0
    objectives: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    learning_goals: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    raw: dict = field(default_factory=dict)

    @property
    def primary_topic(self) -> str:
        """The main topic label for this day (its own title)."""
        return self.topics[0] if self.topics else self.title

    def to_dict(self) -> dict:
        return {
            "day_number": self.day_number,
            "title": self.title,
            "module": self.module,
            "module_number": self.module_number,
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
        self._data_dir = data_dir
        self._path: Path | None = None
        self._days: list[CurriculumDay] = []
        self._modules: list[CurriculumModule] = []
        self._error: str | None = None

    @property
    def path(self) -> Path | None:
        return self._path

    @property
    def error(self) -> str | None:
        return self._error

    @property
    def is_available(self) -> bool:
        return self._error is None and bool(self._days)

    def load(self) -> list[CurriculumDay]:
        """Load (or reload) the curriculum. Never writes to the dataset."""
        self._path = find_dataset_file(self._data_dir, CURRICULUM_DATASET_NAMES)
        if self._path is None:
            self._error = (
                "curriculum.json not found in the data directory, backend/, "
                "or the project root."
            )
            self._days = []
            self._modules = []
            logger.warning(self._error)
            return self._days

        try:
            with self._path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except json.JSONDecodeError as exc:
            self._error = f"curriculum.json is not valid JSON: {exc}"
            self._days = []
            self._modules = []
            logger.error(self._error)
            return self._days

        self._modules = self._parse_modules(payload)
        days = payload if isinstance(payload, list) else payload.get("days", [])
        if not isinstance(days, list) or not days:
            self._error = "curriculum.json contains no curriculum days"
            self._days = []
            logger.error(self._error)
            return self._days

        self._days = [self._normalise_day(index, day) for index, day in enumerate(days)]
        self._error = None
        logger.info(
            "Curriculum loaded: %d days, %d modules from %s",
            len(self._days),
            len(self._modules),
            self._path,
        )
        return self._days

    # ------------------------------------------------------------------ internals

    def _parse_modules(self, payload: Any) -> list[CurriculumModule]:
        modules = payload.get("modules") if isinstance(payload, dict) else None
        parsed: list[CurriculumModule] = []
        if not isinstance(modules, list):
            return parsed
        for module in modules:
            if not isinstance(module, dict):
                continue
            days = module.get("days")
            if not isinstance(days, list) or len(days) != 2:
                continue
            try:
                parsed.append(
                    CurriculumModule(
                        number=int(module.get("n") or 0),
                        title=str(module.get("title") or ""),
                        day_start=int(days[0]),
                        day_end=int(days[1]),
                    )
                )
            except (TypeError, ValueError):
                continue
        return parsed

    def _normalise_day(self, index: int, day: Any) -> CurriculumDay:
        if not isinstance(day, dict):
            day = {"title": str(day)}
        day_number = _pick(day, _DAY_KEYS)
        if day_number is None:
            day_number = index + 1
        title = str(_pick(day, _TITLE_KEYS) or f"Day {day_number}")
        topics = _as_str_list(_pick(day, _TOPICS_KEYS))
        if not topics:
            # No explicit topics in the dataset: the day's own title is the
            # primary topic.  Never invent anything beyond the file's words.
            topics = [title]
        module_title, module_number = self._module_for(int(day_number))
        return CurriculumDay(
            day_number=int(day_number),
            title=title,
            module=module_title or str(_pick(day, _MODULE_KEYS) or ""),
            module_number=module_number,
            objectives=_as_str_list(_pick(day, _OBJECTIVES_KEYS)),
            tools=_as_str_list(_pick(day, _TOOLS_KEYS)),
            learning_goals=_as_str_list(_pick(day, _LEARNING_KEYS)),
            topics=topics,
            raw=day,
        )

    def _module_for(self, day_number: int) -> tuple[str, int]:
        for module in self._modules:
            if module.day_start <= day_number <= module.day_end:
                return module.title, module.number
        return "", 0

    # ------------------------------------------------------------------ readers

    def get_day(self, index: int) -> CurriculumDay | None:
        if 0 <= index < len(self._days):
            return self._days[index]
        return None

    @property
    def days(self) -> list[CurriculumDay]:
        return list(self._days)

    @property
    def modules(self) -> list[CurriculumModule]:
        return list(self._modules)

    @property
    def count(self) -> int:
        return len(self._days)
