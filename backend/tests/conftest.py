"""Pytest fixtures.

Sets the data directory to the bundled fixture datasets and forces the
deterministic mock LLM provider so the whole suite runs offline and fast.
Environment is configured before any application import so the config module
picks it up.
"""
from __future__ import annotations

import os
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

os.environ["AI_DATA_DIR"] = str(FIXTURES_DIR)
os.environ["LLM_MOCK_MODE"] = "true"
os.environ["LLM_API_KEY"] = ""
os.environ.setdefault("INTERVIEW_MIN_QUESTIONS", "8")
os.environ.setdefault("INTERVIEW_MIN_DAYS", "4")
os.environ.setdefault("INTERVIEW_TOTAL_QUESTIONS", "10")
os.environ.setdefault("INTERVIEW_MAX_QUESTIONS", "12")
os.environ.setdefault("SESSION_TTL_SECONDS", "3600")
