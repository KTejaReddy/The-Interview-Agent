"""Curriculum retriever.

Given a day index or topic name, returns the verbatim curriculum content
(objectives, tools, module, learning goals and topics) for that day.  The
retriever never invents curriculum: if a topic is not found, it returns an
empty result instead of guessing.
"""
from __future__ import annotations

from typing import Any

from retrieval.curriculum_loader import CurriculumDay, CurriculumLoader


class CurriculumRetriever:
    """Read-only facade over the loaded curriculum."""

    def __init__(self, loader: CurriculumLoader) -> None:
        self._loader = loader

    @property
    def available(self) -> bool:
        return self._loader.is_available

    @property
    def day_count(self) -> int:
        return self._loader.count

    def get_day(self, index: int) -> CurriculumDay | None:
        return self._loader.get_day(index)

    def all_days(self) -> list[CurriculumDay]:
        return self._loader.days

    def day_content(self, index: int) -> dict[str, Any] | None:
        """Full verbatim content block for a day (or None)."""
        day = self._loader.get_day(index)
        if day is None:
            return None
        return day.to_dict()

    def find_day_for_topic(self, topic: str) -> int | None:
        """Return the first day index that mentions ``topic`` (case-insensitive)."""
        needle = topic.strip().lower()
        for index, day in enumerate(self._loader.days):
            haystack = " ".join(
                [day.title, day.module, *day.topics, *day.objectives]
            ).lower()
            if needle and needle in haystack:
                return index
        return None

    def ground_context(self, day_index: int) -> str:
        """Compact curriculum block used to ground LLM question generation."""
        day = self._loader.get_day(day_index)
        if day is None:
            return ""
        lines = [
            f"DAY: {day.title}",
            f"MODULE: {day.module or '—'}",
            f"OBJECTIVES: {'; '.join(day.objectives) or '—'}",
            f"TOOLS: {', '.join(day.tools) or '—'}",
            f"LEARNING GOALS: {'; '.join(day.learning_goals) or '—'}",
            f"TOPICS: {', '.join(day.topics) or '—'}",
        ]
        return "\n".join(lines)
