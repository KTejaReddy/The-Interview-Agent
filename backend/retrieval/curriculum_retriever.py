"""Curriculum retriever.

Given a day index (or day number) returns the verbatim curriculum content
(objectives, tools, module, learning goals and topics) for that day.  The
retriever never invents curriculum: if a topic is not found, it returns an
empty result instead of guessing.
"""
from __future__ import annotations

import re
from typing import Any

from retrieval.curriculum_loader import CurriculumDay, CurriculumModule, CurriculumLoader

#: Words that carry no topical signal when scanning a candidate's answer.
_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "for", "of", "to", "in", "on",
    "with", "it", "is", "was", "are", "were", "i", "we", "you", "they",
    "that", "this", "these", "those", "how", "what", "when", "where", "why",
}


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

    @property
    def modules(self) -> list[CurriculumModule]:
        return self._loader.modules

    def get_day(self, index: int) -> CurriculumDay | None:
        return self._loader.get_day(index)

    def all_days(self) -> list[CurriculumDay]:
        return self._loader.days

    def day_index_by_number(self, day_number: int) -> int | None:
        """0-based list index for a curriculum day number (e.g. 7 -> idx)."""
        for index, day in enumerate(self._loader.days):
            if day.day_number == day_number:
                return index
        return None

    def get_day_by_number(self, day_number: int) -> CurriculumDay | None:
        index = self.day_index_by_number(day_number)
        return self._loader.get_day(index) if index is not None else None

    def module_for_day(self, index: int) -> CurriculumModule | None:
        day = self._loader.get_day(index)
        if day is None or day.module_number == 0:
            return None
        for module in self._loader.modules:
            if module.number == day.module_number:
                return module
        return None

    def are_adjacent_days(self, index_a: int, index_b: int) -> bool:
        """True when two days belong to the same or neighbouring modules."""
        module_a = self.module_for_day(index_a)
        module_b = self.module_for_day(index_b)
        if module_a is None or module_b is None:
            return False
        return abs(module_a.number - module_b.number) <= 1

    def day_content(self, index: int) -> dict[str, Any] | None:
        """Full verbatim content block for a day (or None)."""
        day = self._loader.get_day(index)
        if day is None:
            return None
        return day.to_dict()

    def find_day_for_topic(self, topic: str) -> int | None:
        """Return the first day index that mentions ``topic`` (case-insensitive)."""
        needle = topic.strip().lower()
        if not needle:
            return None
        for index, day in enumerate(self._loader.days):
            haystack = " ".join(
                [day.title, day.module, *day.topics, *day.objectives]
            ).lower()
            if needle in haystack:
                return index
        return None

    def find_mentions(self, text: str) -> list[str]:
        """Curriculum concepts the candidate's answer refers to.

        Scans the answer for day titles, tool names and meaningful objective
        keywords so later questions can naturally reference what the
        candidate brought up (context retention across the interview).
        """
        if not text:
            return []
        lower = text.lower()
        mentions: list[str] = []
        for day in self._loader.days:
            if day.title.lower() in lower:
                mentions.append(day.title)
            for topic in day.topics:
                if len(topic) >= 4 and topic.lower() in lower:
                    mentions.append(topic)
            for tool in day.tools:
                if len(tool) >= 4 and tool.lower() in lower:
                    mentions.append(tool)
        seen: list[str] = []
        for mention in mentions:
            if mention not in seen:
                seen.append(mention)
        return seen

    def ground_context(self, index: int) -> str:
        """Compact curriculum block used to ground LLM question generation."""
        day = self._loader.get_day(index)
        if day is None:
            return ""
        lines = [
            f"DAY {day.day_number}: {day.title}",
            f"MODULE: {day.module or '—'}",
            f"OBJECTIVES: {'; '.join(day.objectives) or '—'}",
            f"TOOLS: {', '.join(day.tools) or '—'}",
            f"LEARNING GOALS: {'; '.join(day.learning_goals) or '—'}",
        ]
        return "\n".join(lines)

    def keyword_tokens(self) -> set[str]:
        """Every meaningful curriculum word, used for mention scanning."""
        tokens: set[str] = set()
        for day in self._loader.days:
            for chunk in [day.title, *day.topics, *day.tools, *day.objectives]:
                for word in re.split(r"[^a-z0-9]+", chunk.lower()):
                    if len(word) >= 4 and word not in _STOPWORDS:
                        tokens.add(word)
        return tokens
