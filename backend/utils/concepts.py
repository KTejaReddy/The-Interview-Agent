"""Curriculum concept derivation.

The official curriculum days have titles that are course labels ("Embeddings
Explained", "VS Code & Python Environment Setup") and lists of learning
objectives ("Understand how text is converted into vector embeddings",
"Create a /chat API endpoint for the healthcare chatbot").

Interview questions must never be phrased as "What is <Day title>?".  This
module derives a *technical concept phrase* from a learning objective so the
question generator can ask about the actual concept:

* objectives that open with a cognitive verb ("Understand", "Learn", ...)
  lose the verb:  "Understand how text is converted into vector embeddings"
  -> "how text is converted into vector embeddings",
* everything else (the dataset is mostly imperative: "Create", "Build",
  "Validate", ...) becomes an actionable phrase:  "Create a /chat API
  endpoint for the healthcare chatbot" -> "the process of creating a /chat
  API endpoint for the healthcare chatbot".

Both forms read naturally inside "explain / walk me through / the team
needs ..." templates, and both come exclusively from the curriculum's own
wording — nothing is invented.
"""
from __future__ import annotations

from models.enums import QuestionType

#: Verbs that open a *cognitive* objective; stripping them yields a "how …"
#: clause that reads naturally after "explain / walk me through".
_COGNITIVE_VERBS = frozenset(
    {
        "understand", "learn", "know", "explain", "describe", "identify",
        "recognize", "recall", "appreciate", "review",
    }
)


def concept_from_objective(objective: str) -> str:
    """A natural concept phrase for a learning objective.

    * cognitive verb ("Understand ...") -> "how text is converted into
      vector embeddings",
    * imperative ("Create ...")         -> "how to create a /chat API
      endpoint for the healthcare chatbot".

    Both read naturally inside "explain / walk me through / describe ...".
    """
    text = objective.strip().strip(".").strip()
    if not text:
        return ""
    words = text.split()
    first = words[0].lower()
    if first in _COGNITIVE_VERBS:
        rest = " ".join(words[1:]).strip()
        if rest:
            return rest[0].lower() + rest[1:]
        return text
    return "how to " + text[0].lower() + text[1:]


_IRREGULAR_GERUNDS = {
    "run": "running", "split": "splitting", "set": "setting",
    "get": "getting", "stop": "stopping", "put": "putting",
    "begin": "beginning", "forget": "forgetting", "cut": "cutting",
    "hit": "hitting", "plan": "planning", "drop": "dropping",
    "debug": "debugging", "embed": "embedding", "scan": "scanning",
    "log": "logging", "pin": "pinning", "tag": "tagging",
}

#: Verb stems the curriculum opens objectives with (derived from the actual
#: dataset, plus a few chain verbs such as "activate", "debug", "normalize").
_VERB_STEMS = frozenset(
    {
        "create", "build", "implement", "validate", "evaluate", "verify",
        "connect", "store", "compare", "test", "add", "configure",
        "generate", "load", "document", "perform", "identify", "prepare",
        "measure", "install", "convert", "analyze", "integrate", "run",
        "confirm", "scaffold", "initialize", "write", "extract", "scrape",
        "clean", "split", "attach", "export", "visualize", "set", "select",
        "merge", "activate", "debug", "normalize", "commit", "publish",
        "review", "ensure", "finalize", "maintain", "organize", "define",
        "update", "improve", "deploy", "monitor", "simplify", "design",
        "explain", "understand", "learn", "know", "describe", "recognize",
        "recall", "appreciate", "explore", "reuse", "collect", "parse",
        "chunk", "embed", "query", "retrieve", "rank", "search", "summarize",
    }
)


def _gerund(verb: str) -> str:
    """Deterministic gerund form for the small verb set the curriculum uses."""
    lowered = verb.lower()
    if lowered in _IRREGULAR_GERUNDS:
        return _IRREGULAR_GERUNDS[lowered]
    if lowered.endswith("ie"):
        return lowered[:-2] + "ying"
    if lowered.endswith("e") and len(lowered) > 2:
        return lowered[:-1] + "ing"
    if len(lowered) == 3 and lowered[-2] in "aeiou" and lowered[-1] not in "aeiou":
        return lowered + lowered[-1] + "ing"
    return lowered + "ing"


def action_phrase_from_objective(objective: str) -> str:
    """The objective as an activity noun phrase (gerund form).

    "Create a /chat API endpoint for the healthcare chatbot" ->
    "creating a /chat API endpoint for the healthcare chatbot".
    "Understand how text is converted into vector embeddings" ->
    "understanding how text is converted into vector embeddings".
    "Run and debug your first Python program inside VS Code" ->
    "running and debugging your first Python program inside VS Code".

    Reads naturally after "the team is tasked with ...", "owns ...",
    "production issues with ...".  Verb chains joined by "and" / "," are
    gerunded together; non-verbs stop the chain.
    """
    text = objective.strip().strip(".").strip()
    if not text:
        return ""
    words = text.split()
    output: list[str] = []
    in_chain = True
    for word in words:
        cleaned = word.rstrip(",;.")
        lowered = cleaned.lower()
        if in_chain and lowered in _VERB_STEMS:
            punct = word[len(cleaned):]
            output.append(_gerund(cleaned) + punct)
            continue
        output.append(word)
        if not (lowered == "and" or word.endswith(",")):
            in_chain = False
    return " ".join(output)

#: Cognitive level ladder used in the QuestionIntent (8 levels).
_COGNITIVE_LABELS: dict[QuestionType, str] = {
    QuestionType.DEFINITION: "Level 1 — concept recognition",
    QuestionType.CONCEPTUAL: "Level 2 — explanation",
    QuestionType.SCENARIO: "Level 3 — application",
    QuestionType.REASONING: "Level 3 — application reasoning",
    QuestionType.DEBUGGING: "Level 5 — debugging",
    QuestionType.TRADEOFFS: "Level 6 — trade-off",
    QuestionType.ARCHITECTURE: "Level 7 — architecture",
    QuestionType.DESIGN: "Level 7 — design",
    QuestionType.PRODUCTION: "Level 8 — production reasoning",
    QuestionType.DEPLOYMENT: "Level 8 — deployment",
}


def cognitive_label(question_type: QuestionType) -> str:
    """Human label for the cognitive level a question type targets."""
    return _COGNITIVE_LABELS.get(question_type, question_type.value)


#: Why the interviewer asks this question type (what we want to learn).
_PURPOSES: dict[QuestionType, str] = {
    QuestionType.DEFINITION: (
        "establish whether the candidate can articulate the concept in their "
        "own words rather than parroting a label"
    ),
    QuestionType.CONCEPTUAL: (
        "establish whether the candidate can explain the concept and how it "
        "fits the pipeline they built"
    ),
    QuestionType.SCENARIO: (
        "establish whether the candidate can apply the concept to a concrete, "
        "realistic situation"
    ),
    QuestionType.REASONING: (
        "establish whether the candidate can reason about when to reach for "
        "the concept and when to avoid it"
    ),
    QuestionType.ARCHITECTURE: (
        "establish whether the candidate can place the concept in a system "
        "architecture and justify that placement"
    ),
    QuestionType.DEBUGGING: (
        "establish whether the candidate can diagnose failures involving the "
        "concept in production"
    ),
    QuestionType.TRADEOFFS: (
        "establish whether the candidate can weigh the trade-offs around the "
        "concept against simpler alternatives"
    ),
    QuestionType.DESIGN: (
        "establish whether the candidate can design a small feature around "
        "the concept (components and data flows)"
    ),
    QuestionType.PRODUCTION: (
        "establish whether the candidate can reason about the concept running "
        "in production (monitoring, failure modes)"
    ),
    QuestionType.DEPLOYMENT: (
        "establish whether the candidate can reason about shipping and "
        "rolling back changes that touch the concept"
    ),
}


def purpose_for_type(question_type: QuestionType) -> str:
    """One-line statement of what the question type wants to learn."""
    return _PURPOSES[question_type]


#: What a correct answer to each question type must contain (internal bar).
_EXPECTED_EVIDENCE: dict[QuestionType, list[str]] = {
    QuestionType.DEFINITION: [
        "defines the concept in their own words",
        "connects it to the cohort pipeline",
    ],
    QuestionType.CONCEPTUAL: [
        "explains the concept correctly",
        "shows how it interacts with neighbouring parts of the pipeline",
    ],
    QuestionType.SCENARIO: [
        "describes a concrete, realistic approach",
        "mentions the first concrete step they would take",
    ],
    QuestionType.REASONING: [
        "gives at least one situation where the concept is the right tool",
        "gives at least one situation where it is the wrong tool",
    ],
    QuestionType.ARCHITECTURE: [
        "places the concept in the architecture",
        "justifies the placement in one or two sentences",
    ],
    QuestionType.DEBUGGING: [
        "names a first diagnostic step",
        "follows it with a plausible next check",
    ],
    QuestionType.TRADEOFFS: [
        "names a genuine trade-off",
        "explains how they would decide",
    ],
    QuestionType.DESIGN: [
        "lists the key components",
        "describes the data flow between them",
    ],
    QuestionType.PRODUCTION: [
        "names a concrete production risk",
        "suggests how to detect or mitigate it",
    ],
    QuestionType.DEPLOYMENT: [
        "names a safe rollout step",
        "explains how they would roll back",
    ],
}


def expected_evidence_for_type(question_type: QuestionType) -> list[str]:
    """The evidence bar a good answer to this question type must meet."""
    return _EXPECTED_EVIDENCE[question_type]
