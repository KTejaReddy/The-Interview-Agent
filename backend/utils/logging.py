"""Centralised logging configuration.

Every module logs through the root logger configured here so that log
format, level and destination stay consistent across the service.
"""
from __future__ import annotations

import logging
import sys

from config import Settings

_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | "
    "%(message)s"
)


def configure_logging(settings: Settings) -> None:
    """Configure the root logger once per process."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT))
    root = logging.getLogger()
    root.setLevel(level)
    # Avoid duplicate handlers on hot reload.
    root.handlers = [handler]
    # Keep uvicorn's access logs readable.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a child logger for the given module name."""
    return logging.getLogger(name)
