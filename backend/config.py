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
    min_questions: int = int(os.getenv("INTERVIEW_MIN_QUESTIONS", "8"))
    min_days: int = int(os.getenv("INTERVIEW_MIN_DAYS", "4"))
    total_questions: int = int(os.getenv("INTERVIEW_TOTAL_QUESTIONS", "12"))
    max_follow_ups_per_question: int = int(
        os.getenv("INTERVIEW_MAX_FOLLOW_UPS", "2")
    )
    session_ttl_seconds: int = int(os.getenv("SESSION_TTL_SECONDS", "7200"))
    max_history_turns: int = int(os.getenv("MAX_HISTORY_TURNS", "12"))

    # --- LLM provider abstraction -----------------------------------------
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai_compatible")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    llm_max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "800"))
    llm_timeout_seconds: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
    # When true the LLM service uses a deterministic offline provider that
    # requires no API key.  Useful for demos and tests only.
    llm_mock_mode: bool = _env_bool("LLM_MOCK_MODE", False)
    # Some providers (e.g. Gemini) do not support the response_format
    # parameter.  Set to empty string or "none" to disable it.
    llm_json_mode: bool = _env_bool("LLM_JSON_MODE", True)

    @property
    def llm_configured(self) -> bool:
        """True when a live provider can be used (key present)."""
        return bool(self.llm_api_key) or self.llm_mock_mode


settings = Settings()
