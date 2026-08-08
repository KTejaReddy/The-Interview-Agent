"""The dedicated human-interviewer prompt block.

``prompts/human_interviewer.md`` is the single authoritative home for how
the interviewer behaves.  It must be loaded, composed into the system
prompt that every interviewer generation path receives, and the per-task
templates must keep their dispatch markers (the LLM service routes on
those markers).
"""

from config import Settings
from services.prompt_builder import PromptBuilder


def _builder() -> PromptBuilder:
    return PromptBuilder(Settings())


def test_human_interviewer_block_is_loaded() -> None:
    block = _builder().human_interviewer_prompt()
    low = block.lower()
    assert "highly experienced human technical interviewer" in low
    assert "contradicts themselves" in low


def test_system_prompt_composes_block_plus_contract() -> None:
    system = _builder().system_prompt()
    low = system.lower()
    # The behavioral block is present...
    assert "highly experienced human technical interviewer" in low
    assert "contradicts themselves" in low
    # ...and so is the engine contract + security rules.
    assert "engine contract" in low
    assert "non-negotiable" in low
    assert "untrusted data" in low


def test_assessment_prompt_is_lean() -> None:
    """Internal assessment calls (evaluate, feedback) get the contract and
    security but not the full persona — it would add ~3.6K tokens per call
    to a structured-verdict task."""
    builder = _builder()
    lean = builder.assessment_system_prompt()
    assert "non-negotiable" in lean.lower()
    assert "untrusted data" in lean.lower()
    assert "real human technical interviewer" not in lean.lower()
    assert len(lean) < len(builder.system_prompt()) // 2


def test_generation_templates_keep_dispatch_markers() -> None:
    """The LLM service classifies each call by these markers — they must
    survive the de-duplication against the new behavioral block."""
    templates = _builder()._templates
    assert "Generate ONE interview question" in templates["generate_question"]
    assert "Evaluate the candidate" in templates["evaluate_answer"]
    assert "Follow-up strategy" in templates["generate_follow_up"]
    assert "CANDIDATE'S ANSWER" in templates["evaluate_answer"]


def test_dangling_connector_stripped_from_reaction() -> None:
    """The engine appends the question after the LLM reaction; a reaction
    left dangling on a connector ("...embeddings, but") must be cleaned so
    the assembled line never reads "...but What problem does X?"."""
    builder = _builder()
    out = builder.reaction_or_fallback(
        "That's an interesting approach with embeddings, but",
        topic="MCP",
        index=1,
    )
    assert out == "That's an interesting approach with embeddings."
    # Legitimate reactions are untouched.
    assert builder.reaction_or_fallback(
        "Okay, that's interesting.", topic="MCP", index=1
    ) == "Okay, that's interesting."
    assert builder.reaction_or_fallback(
        "What about retrieval?", topic="MCP", index=1
    ) == "What about retrieval?"


def test_reaction_gets_terminal_punctuation() -> None:
    """The engine appends the question after the reaction; without a
    trailing period the line would read "Let's shift gears What problem
    does..."."""
    builder = _builder()
    assert builder.reaction_or_fallback(
        "Let's shift gears", topic="MCP", index=1
    ) == "Let's shift gears."
    # Already punctuated reactions are left alone.
    assert builder.reaction_or_fallback(
        "Right.", topic="MCP", index=1
    ) == "Right."


def test_behavior_not_duplicated_in_question_template() -> None:
    """Persona-level rules now live only in the dedicated block, not
    re-injected verbatim into the per-task template."""
    question = _builder()._templates["generate_question"]
    assert "Glad to hear it" not in question
    assert "profile metadata" not in question
