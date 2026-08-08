"""Application configuration.

All runtime configuration is read from environment variables (optionally
seeded from a ``.env`` file via python-dotenv).  No secrets are ever
hardcoded here: the LLM API key is read at runtime and defaults to an empty
string so the application starts safely before a key is provisioned.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load environment from the nearest .env file (backend/.env, then project root).
load_dotenv()

# Base directory of the backend package (this file lives in backend/).
BACKEND_DIR = Path(__file__).resolve().parent

#: Accepted dataset filenames.  The official datasets ship as
#: ``candidates.json`` (plural) but ``candidate.json`` is also accepted for
#: backwards compatibility with earlier copies.
CANDIDATE_DATASET_NAMES = ("candidates.json", "candidate.json")
CURRICULUM_DATASET_NAMES = ("curriculum.json",)
SPEC_DATASET_NAMES = ("technical-spec.md", "technical_spec.md")


def find_dataset_file(data_dir: str | Path, names: tuple[str, ...]) -> Path | None:
    """Locate a dataset file across the likely data locations.

    Searches, in order:

    1. ``AI_DATA_DIR`` (the configured data directory),
    2. the backend package directory itself (``backend/``),
    3. the repository root (the parent of ``backend/``).

    The datasets may therefore live in ``backend/data/``, ``backend/`` or at
    the project root — wherever they were dropped in.
    """
    bases = [Path(data_dir), BACKEND_DIR, BACKEND_DIR.parent]
    for base in bases:
        for name in names:
            candidate = base / name
            if candidate.exists() and candidate.is_file():
                return candidate
    return None


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    """Immutable application settings."""

    # --- Application -----------------------------------------------------
    app_name: str = os.getenv("APP_NAME", "AI Interview Agent")
    debug: bool = _env_bool("DEBUG", False)
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # --- CORS ------------------------------------------------------------
    cors_origins: list[str] = field(
        default_factory=lambda: _env_list(
            "CORS_ORIGINS", ["http://localhost:5173", "http://127.0.0.1:5173"]
        )
    )

    # --- Datasets --------------------------------------------------------
    # Directory that holds curriculum.json, candidate.json and
    # technical-spec.md.  The loader NEVER modifies these files.
    data_dir: str = os.getenv("AI_DATA_DIR", str(BACKEND_DIR / "data"))

    # --- Interview parameters ---------------------------------------------
    # MIN is a hard requirement; TARGET is the soft budget the interview
    # finishes at once the minimums are met and evidence is sufficient;
    # MAX is the absolute safety ceiling on main questions.  The interview
    # should feel concise (8-10) and never routinely run to 12+.
    min_questions: int = int(os.getenv("INTERVIEW_MIN_QUESTIONS", "8"))
    min_days: int = int(os.getenv("INTERVIEW_MIN_DAYS", "4"))
    total_questions: int = int(os.getenv("INTERVIEW_TOTAL_QUESTIONS", "10"))
    max_questions: int = int(os.getenv("INTERVIEW_MAX_QUESTIONS", "12"))
    max_follow_ups_per_question: int = int(
        os.getenv("INTERVIEW_MAX_FOLLOW_UPS", "2")
    )
    session_ttl_seconds: int = int(os.getenv("SESSION_TTL_SECONDS", "7200"))
    max_history_turns: int = int(os.getenv("MAX_HISTORY_TURNS", "12"))

    # --- LLM provider abstraction -----------------------------------------
    llm_provider: str = os.getenv("LLM_PROVIDER", "groq")
    llm_base_url: str = os.getenv("GROQ_BASE_URL", os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"))
    llm_model: str = os.getenv("GROQ_MODEL", os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"))
    #: Fast model used for lightweight conversational turns (short follow-ups
    #: on non-substantive verdicts).  Must be an existing configured model —
    #: it defaults to a model already in the fallback chain, so no new API
    #: key or provider is ever required.
    llm_fast_model: str = os.getenv("LLM_FAST_MODEL", "llama-3.1-8b-instant")
    #: Model guard mode for candidate-message security screening.
    #: ``auto`` runs the light guard model only when a message shows soft
    #: signals of an override/extraction attempt (the deterministic input
    #: guard always runs); ``always`` runs the light guard on every message;
    #: ``off`` keeps only the deterministic layer (no guard LLM calls).
    llm_guard_mode: str = os.getenv("LLM_GUARD_MODE", "auto")
    #: Output budget for conversational turns (evaluation / question /
    #: follow-up).  The interviewer answers in 1-3 short sentences, so 800
    #: tokens of headroom only delays every turn; feedback keeps the full
    #: ``llm_max_tokens`` budget.
    llm_turn_max_tokens: int = int(os.getenv("LLM_TURN_MAX_TOKENS", "300"))
    #: Recent turns kept verbatim in prompts; older turns are compressed into
    #: the structured interview memory (aggregate summary + notable
    #: statements), so token count stays flat as the interview grows while
    #: earlier claims, mistakes and contradictions are never lost.
    transcript_window: int = int(os.getenv("TRANSCRIPT_WINDOW", "6"))
    llm_fallback_models: list[str] = field(
        default_factory=lambda: _env_list(
            "LLM_FALLBACK_MODELS",
            [
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "openai/gpt-oss-20b",
                "qwen/qwen3.6-27b",
                "groq/compound-mini",
                "openai/gpt-oss-120b",
                "groq/compound",
                "allam-2-7b",
            ],
        )
    )
    llm_api_key: str = os.getenv("GROQ_API_KEY", os.getenv("LLM_API_KEY", ""))
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    llm_max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "800"))
    llm_timeout_seconds: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
    # When true the LLM service uses a deterministic offline provider that
    # requires no API key.  Useful for demos and tests only.
    llm_mock_mode: bool = _env_bool("LLM_MOCK_MODE", False)
    # Some providers (e.g. Gemini) do not support the response_format
    # parameter.  Set to empty string or "none" to disable it.
    llm_json_mode: bool = _env_bool("LLM_JSON_MODE", True)
    # ------------------------------------------------------------------
    # Quota-aware routing: the router switches models BEFORE a known limit
    # is reached.  ``model_quota_headroom_percent`` is the master knob
    # (e.g. 20 = keep 20% in reserve, switch at 80% usage); the per-limit
    # thresholds override it when set.  All limits come from the Groq
    # account table and live in services/model_router.py (MODEL_QUOTAS).
    model_quota_headroom_percent: int = int(
        os.getenv("MODEL_QUOTA_HEADROOM_PERCENT", "20")
    )
    model_tpm_headroom: float = float(
        os.getenv("MODEL_TPM_HEADROOM", "0.75")
    )
    model_tpd_headroom: float = float(
        os.getenv("MODEL_TPD_HEADROOM", "0.80")
    )
    model_rpm_headroom: float = float(
        os.getenv("MODEL_RPM_HEADROOM", "0.75")
    )
    model_rpd_headroom: float = float(
        os.getenv("MODEL_RPD_HEADROOM", "0.80")
    )

    @property
    def llm_configured(self) -> bool:
        """True when a live provider can be used (key present)."""
        return bool(self.llm_api_key) or self.llm_mock_mode


settings = Settings()
