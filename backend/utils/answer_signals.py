"""Answer signal detectors.

Deterministic, content-based classification of candidate answers used by
both the response evaluator and the mock LLM provider.  Keeping them in one
place guarantees the evaluator's hard rules and the demo provider never
disagree.

The key principle behind this module: **surface phrases are not evidence.**

* ``detects_idk`` — the candidate gave no substantive answer ("I don't
  know", "not sure", "no idea", ...).
* ``detects_claim_without_evidence`` — the candidate asserted knowledge
  ("I know", "yes", "I understand", "of course") **without providing any
  content**.  A claim is never treated as demonstrated competence; it is
  marked for a verify probe instead.  ``"Yes, embeddings map text to
  vectors by meaning..."`` is *not* a bare claim because it contains
  substance.
"""
from __future__ import annotations

import re

#: Phrases indicating the candidate did not attempt an answer.
_IDK_PATTERNS = (
    re.compile(r"\b(i'?m\s+)?not\s+(?:really\s+)?sure\b", re.I),
    re.compile(r"\bi\s+don'?t\s+know\b", re.I),
    re.compile(r"\bi\s+do\s+not\s+know\b", re.I),
    re.compile(r"\bno\s+idea\b", re.I),
    re.compile(r"\bno\s+clue\b", re.I),
    re.compile(r"\bcan'?t\s+(?:really\s+)?(?:recall|remember)\b", re.I),
    re.compile(r"\bdon'?t\s+remember\b", re.I),
    re.compile(r"\bnever\s+heard\s+of\b", re.I),
    re.compile(r"\bi\s+don'?t\s+understand\b", re.I),
    re.compile(r"\bdraw(?:ing)?\s+a\s+blank\b", re.I),
    re.compile(r"\b(?:haven'?t|not)\s+covered\s+(?:that|this|it)\b", re.I),
)

#: Phrases that assert knowledge without demonstrating it.
_CLAIM_PATTERNS = (
    re.compile(r"\bi\s+(?:already\s+)?know\b", re.I),
    re.compile(r"\bi\s+know\s+(?:this|that|it|about)\b", re.I),
    re.compile(r"\bi\s+know\s+how\s+to\b", re.I),
    re.compile(r"\bi\s+(?:do\s+|totally\s+)?understand\b", re.I),
    re.compile(r"\bi'?m\s+(?:very\s+|pretty\s+|quite\s+)?confident\b", re.I),
    re.compile(r"\bi'?m\s+familiar\s+with\b", re.I),
    re.compile(r"\bof\s+course\b", re.I),
    re.compile(r"\byes(?:,\s*i\s+do)?\b", re.I),
    re.compile(r"\byeah\b", re.I),
    re.compile(r"\bdefinitely\b", re.I),
    re.compile(r"\bi\s+got\s+(?:this|it)\b", re.I),
    re.compile(r"\bi'?ve\s+got\s+(?:this|it)\b", re.I),
)

#: Greetings / filler that carry no technical content.  A candidate who
#: answers a technical question with "hello" gets one short, simpler recovery
#: question — never a long explanation about why they didn't answer.
#:
#: Greeting words require the WHOLE answer (so "Hi, similar text…" — a real
#: short answer — is never misrouted), and every bare affirmation ("yes",
#: "yeah", "sure") is a non-answer here: per the interview rules "I know"
#: is a knowledge claim (verify), while "yes"-style fillers get a simpler
#: recovery instead.
_GREETING_PATTERNS = (
    re.compile(r"^\s*(?:hi+|hey+|hello+|hiya|yo|sup|howdy)\s*[,.!]*\s*$", re.I),
    re.compile(r"^\s*good\s+(?:morning|afternoon|evening)\s*[,.!]*\s*$", re.I),
    re.compile(r"^\s*(?:ok|okay|okey|k|hmm+|um+|uh+|ah+|ha+)\s*$", re.I),
    re.compile(r"^\s*(?:thanks|thank\s+you|ty|thx)\s*[,.!]*\s*$", re.I),
    re.compile(r"^\s*(?:yes|yeah|yep|yup|sure|right)\s*[,.!]*\s*$", re.I),
    re.compile(r"^\s*(?:yes|yeah)\s*,?\s+(?:i\s+do|i\s+am|i\s+have|ok|okay|fine)\s*[,.!]*\s*$", re.I),
)

#: A bare claim has to be *short*: any real content disqualifies it.
_MAX_CLAIM_LENGTH = 60


def detects_idk(answer: str) -> bool:
    """True when the answer carries no attempt at substance."""
    if not answer or len(answer.strip()) < 2:
        return True
    return any(pattern.search(answer) for pattern in _IDK_PATTERNS)


def detects_greeting(answer: str) -> bool:
    """True when the answer is a greeting or filler with no content
    ("hello", "hi", "okay", "hmm").  Never the same thing as a knowledge
    claim — the candidate simply did not attempt the question."""
    if not answer:
        return False
    stripped = answer.strip()
    if len(stripped) >= 24:
        return False
    return any(pattern.search(stripped) for pattern in _GREETING_PATTERNS)


def detects_claim_without_evidence(answer: str) -> bool:
    """True when the candidate asserted knowledge but gave no content.

    ``"I know"`` / ``"yes"`` alone → True.  A claim followed by a real
    explanation → False (it is evidence, evaluate it normally).
    """
    if not answer:
        return False
    stripped = answer.strip()
    if len(stripped) >= _MAX_CLAIM_LENGTH:
        return False
    return any(pattern.search(stripped) for pattern in _CLAIM_PATTERNS)
