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
    assert first.day_number == 1
    assert first.title == "Python Fundamentals"
    # No topics field in the dataset -> the day's own title becomes the topic.
    assert first.primary_topic == "Python Fundamentals"
    assert first.objectives
    assert first.tools == ["Python 3", "VS Code"]
    # Module enrichment comes from the file's own modules section.
    assert first.module == "Programming Foundations"
    assert first.module_number == 1


def test_modules_parsed() -> None:
    loader = CurriculumLoader(FIXTURES_DIR)
    loader.load()
    assert [m.number for m in loader.modules] == [1, 2]


def test_retriever_day_number_lookup() -> None:
    loader = CurriculumLoader(FIXTURES_DIR)
    loader.load()
    retriever = CurriculumRetriever(loader)

    index = retriever.day_index_by_number(4)
    assert index == 3
    day = retriever.get_day_by_number(4)
    assert day is not None
    assert day.title == "Databases & SQL"
    assert retriever.day_index_by_number(99) is None


def test_retriever_finds_day_for_topic() -> None:
    loader = CurriculumLoader(FIXTURES_DIR)
    loader.load()
    retriever = CurriculumRetriever(loader)

    index = retriever.find_day_for_topic("Databases")
    assert index == 3
    assert retriever.find_day_for_topic("nonexistent-topic-xyz") is None


def test_module_adjacency() -> None:
    loader = CurriculumLoader(FIXTURES_DIR)
    loader.load()
    retriever = CurriculumRetriever(loader)

    # Day 2 (module 1) and day 4 (module 2) are neighbouring modules.
    assert retriever.are_adjacent_days(1, 3) is True
    # Day 4 and day 5 are the same module.
    assert retriever.are_adjacent_days(3, 4) is True


def test_mentions_finder() -> None:
    loader = CurriculumLoader(FIXTURES_DIR)
    loader.load()
    retriever = CurriculumRetriever(loader)

    mentions = retriever.find_mentions(
        "I used Docker and CI/CD for deployment, and wrote SQL for the database."
    )
    assert "Docker" in mentions
    assert "CI/CD" in mentions or "Deployment & Production" in mentions


def test_ground_context_never_hallucinates() -> None:
    loader = CurriculumLoader(FIXTURES_DIR)
    loader.load()
    retriever = CurriculumRetriever(loader)

    context = retriever.ground_context(3)
    assert "DAY 4" in context
    assert "DATABASES" in context.upper()

    assert retriever.ground_context(99) == ""


def test_tolerant_alternate_spellings() -> None:
    import json

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
        assert days[0].day_number == 7
        assert days[0].title == "Testing"
        assert days[0].module == "Quality"
        assert days[0].topics == ["unit-tests", "mocks"]
        assert "Write unit tests" in days[0].objectives
        assert days[0].tools == ["pytest"]
    finally:
        (tmp / "curriculum.json").unlink()
        tmp.rmdir()
