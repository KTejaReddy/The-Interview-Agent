"""Tests for the curriculum loader and retriever."""
from __future__ import annotations

from retrieval.curriculum_loader import CurriculumLoader
from retrieval.curriculum_retriever import CurriculumRetriever
from tests.conftest import FIXTURES_DIR


def test_loads_fixture_curriculum() -> None:
    loader = CurriculumLoader(FIXTURES_DIR)
    days = loader.load()

    assert loader.is_available
    assert len(days) == 6
    first = days[0]
    assert first.title == "Python Fundamentals"
    assert "python-loops" in first.topics
    assert first.objectives
    assert first.tools == ["Python 3", "VS Code"]


def test_retriever_finds_day_for_topic() -> None:
    loader = CurriculumLoader(FIXTURES_DIR)
    loader.load()
    retriever = CurriculumRetriever(loader)

    index = retriever.find_day_for_topic("oops-classes")
    assert index == 1
    day = retriever.get_day(index)
    assert day is not None
    assert "oops-inheritance" in day.topics

    assert retriever.find_day_for_topic("nonexistent-topic-xyz") is None


def test_ground_context_never_hallucinates() -> None:
    loader = CurriculumLoader(FIXTURES_DIR)
    loader.load()
    retriever = CurriculumRetriever(loader)

    context = retriever.ground_context(3)
    assert "DATABASES" in context.upper()
    assert "db-indexes" in context

    assert retriever.ground_context(99) == ""


def test_tolerant_alternate_spellings() -> None:
    import json

    import pytest

    tmp = FIXTURES_DIR.parent / "_tmp_alt"
    tmp.mkdir(exist_ok=True)
    (tmp / "curriculum.json").write_text(
        json.dumps(
            {
                "days": [
                    {
                        "number": 7,
                        "name": "Testing",
                        "unit": "Quality",
                        "learning_objectives": ["Write unit tests"],
                        "tooling": ["pytest"],
                        "outcomes": ["Test everything"],
                        "subtopics": ["unit-tests", "mocks"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    try:
        loader = CurriculumLoader(tmp)
        days = loader.load()
        assert days[0].day_id == 7
        assert days[0].title == "Testing"
        assert days[0].module == "Quality"
        assert days[0].topics == ["unit-tests", "mocks"]
        assert "Write unit tests" in days[0].objectives
        assert days[0].tools == ["pytest"]
    finally:
        (tmp / "curriculum.json").unlink()
        tmp.rmdir()
