"""Tests for the deterministic semantic duplicate guard."""
from __future__ import annotations

from agents.duplicate_guard import cosine, first_duplicate_index, is_duplicate, jaccard, normalize
from models.enums import QuestionType


def test_normalize_removes_stopwords() -> None:
    tokens = normalize("What is the purpose of embeddings?")
    assert "what" not in tokens
    assert "embeddings" in tokens
    assert "purpose" in tokens


def test_jaccard_similarity() -> None:
    assert jaccard(normalize("a b c"), normalize("a b c")) == 1.0
    assert jaccard(normalize("a b c"), normalize("d e f")) == 0.0
    similarity = jaccard(normalize("embeddings vectors"), normalize("embeddings search"))
    assert 0.0 < similarity < 1.0


def test_cosine_similarity() -> None:
    assert cosine(normalize("explain embeddings"), normalize("explain embeddings")) == 1.0
    assert cosine(normalize("explain embeddings"), normalize("deploy containers")) < 0.3


def test_identical_question_is_duplicate() -> None:
    question = "Could you explain how embeddings map text into vectors?"
    assert is_duplicate(question, [question])


def test_paraphrase_is_duplicate() -> None:
    previous = "Explain what embeddings are and how they map text into vectors."
    candidate = "Could you tell me what embeddings are and how text maps into vectors?"
    assert is_duplicate(candidate, [previous])


def test_different_topic_not_duplicate() -> None:
    assert not is_duplicate(
        "How would you deploy a container to production?",
        ["Explain what embeddings are and how they map text into vectors."],
    )


def test_same_topic_same_type_is_duplicate() -> None:
    previous = "What are embeddings and what do they do?"
    candidate = "Can you explain the purpose of embeddings?"
    assert is_duplicate(
        candidate,
        [previous],
        candidate_type=QuestionType.CONCEPTUAL,
        previous_types=[QuestionType.CONCEPTUAL],
        candidate_topic="Embeddings",
        previous_topics=["Embeddings"],
    )


def test_same_topic_different_type_not_duplicate() -> None:
    previous = "What are embeddings and what do they do?"
    candidate = "A teammate's embedding search returns bad results — how would you debug it?"
    assert not is_duplicate(
        candidate,
        [previous],
        candidate_type=QuestionType.DEBUGGING,
        previous_types=[QuestionType.CONCEPTUAL],
        candidate_topic="Embeddings",
        previous_topics=["Embeddings"],
    )


def test_first_duplicate_index() -> None:
    questions = [
        "Explain what embeddings are.",
        "How do you deploy a container?",
    ]
    assert first_duplicate_index("Tell me what embeddings are.", questions) == 0
    assert first_duplicate_index("How do you scale a database?", questions) is None
