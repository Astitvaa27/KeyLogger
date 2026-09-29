"""Centralized logging configuration.

Provides detailed, timestamped logs to both the console and a rotating file
under the lab's log directory. Keeping logs verbose supports reproducible
experiments and post-hoc analysis.
"""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_CONSOLE_FMT = "%(asctime)s [%(levelname)-7s] %(name)s: %(message)s"
_FILE_FMT = "%(asctime)s [%(levelname)-7s] %(name)s (%(module)s:%(lineno)d): %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"

_configured = False


def configure_logging(log_dir: Path | None = None, level: str = "INFO") -> logging.Logger:
    """Configure the root 'klab' logger. Safe to call multiple times."""
    global _configured
    logger = logging.getLogger("klab")
    if _configured:
        logger.setLevel(level.upper())
        return logger

    logger.setLevel(level.upper())
    logger.propagate = False

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(_CONSOLE_FMT, _DATE_FMT))
    console.setLevel(level.upper())
    logger.addHandler(console)

    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_dir / "klab.log", maxBytes=1_000_000, backupCount=5, encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter(_FILE_FMT, _DATE_FMT))
        file_handler.setLevel(logging.DEBUG)  # file always captures full detail
        logger.addHandler(file_handler)

    _configured = True
    return logger


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the 'klab' namespace."""
    return logging.getLogger(f"klab.{name}")
