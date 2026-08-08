"""Semantic duplicate guard.

Prevents the interviewer from asking effectively the same question twice,
using deterministic text-similarity checks rather than relying only on an
LLM instruction.

Two questions are considered duplicates when:

* their token-set Jaccard similarity is high (>= ``_JACCARD_HARD``), or
* they share the same topic AND the same cognitive task (question type)
  AND have moderate token overlap (>= ``_JACCARD_SOFT``).

The guard is also used on follow-ups: a follow-up that is too close to any
previous question is rejected so the interviewer must add a new dimension
(application, scenario, debugging, trade-off, ...) instead of re-asking.
"""
from __future__ import annotations

import re
from collections import Counter

from models.enums import QuestionType

_STOPWORDS = frozenset(
    """
    a an the and or but if then else for of to in on with without about
    what which who whom whose when where why how is are was were be been
    being do does did have has had can could would should may might must
    you your yours i me my we our us they them their this that these those
    it its there here not no dont doesn didnt cant couldnt wouldnt
    explain tell describe walk through let us lets can you could you
    would you please also just very really much more most some any all
    one two three first second third thing things way ways example examples
    """.split()
)

_WORD_RE = re.compile(r"[a-z0-9']+")


def normalize(text: str) -> list[str]:
    """Lowercase tokens with stopwords removed."""
    tokens = _WORD_RE.findall(text.lower())
    return [token for token in tokens if token not in _STOPWORDS]


def jaccard(a: list[str], b: list[str]) -> float:
    """Token-set Jaccard similarity in [0, 1]."""
    if not a or not b:
        return 0.0
    set_a, set_b = set(a), set(b)
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


def cosine(a: list[str], b: list[str]) -> float:
    """Token-count cosine similarity in [0, 1]."""
    if not a or not b:
        return 0.0
    counter_a, counter_b = Counter(a), Counter(b)
    keys = set(counter_a) | set(counter_b)
    dot = sum(counter_a[k] * counter_b[k] for k in keys)
    norm_a = sum(v * v for v in counter_a.values()) ** 0.5
    norm_b = sum(v * v for v in counter_b.values()) ** 0.5
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


#: Above this Jaccard value a question is a hard duplicate regardless of type.
_JACCARD_HARD = 0.62
#: Same topic + same type with at least this Jaccard is also a duplicate.
_JACCARD_SOFT = 0.38
#: Cosine floor for same topic + same type (catches longer rewordings).
_COSINE_SOFT = 0.55
#: Same topic alone with this combination of overlap counts as a duplicate
#: even without question-type metadata (e.g. consecutive follow-ups that
#: share a template but differ only in the quoted answer snippet).
_JACCARD_TOPIC = 0.45
_COSINE_TOPIC = 0.62


def is_duplicate(
    candidate_text: str,
    previous_texts: list[str],
    *,
    candidate_type: QuestionType | None = None,
    previous_types: list[QuestionType | None] | None = None,
    candidate_topic: str = "",
    previous_topics: list[str] | None = None,
) -> bool:
    """Deterministic duplicate check against every previous question.

    ``previous_texts`` should include every question asked so far (main
    questions and follow-ups).
    """
    cand_tokens = normalize(candidate_text)
    if not cand_tokens:
        return False

    for index, previous in enumerate(previous_texts):
        prev_tokens = normalize(previous)
        jac = jaccard(cand_tokens, prev_tokens)
        if jac >= _JACCARD_HARD:
            return True

        prev_type = (
            previous_types[index]
            if previous_types and index < len(previous_types)
            else None
        )
        prev_topic = (
            previous_topics[index]
            if previous_topics and index < len(previous_topics)
            else ""
        )
        same_type = prev_type is not None and candidate_type is not None and prev_type == candidate_type
        same_topic = bool(prev_topic and candidate_topic and prev_topic == candidate_topic)
        cos = cosine(cand_tokens, prev_tokens)
        if (same_topic and same_type) and (jac >= _JACCARD_SOFT or cos >= _COSINE_SOFT):
            return True
        # Same topic + strong lexical overlap is a duplicate even when the
        # question type metadata is missing (follow-ups).
        if same_topic and jac >= _JACCARD_TOPIC and cos >= _COSINE_TOPIC:
            return True

    return False


def first_duplicate_index(
    candidate_text: str, previous_texts: list[str]
) -> int | None:
    """Index of the first previous question that duplicates the candidate."""
    cand_tokens = normalize(candidate_text)
    for index, previous in enumerate(previous_texts):
        if jaccard(cand_tokens, normalize(previous)) >= _JACCARD_HARD:
            return index
    return None
