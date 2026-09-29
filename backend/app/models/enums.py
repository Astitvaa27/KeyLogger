"""Shared enumerations used across models and schemas."""
from __future__ import annotations

import enum


class KeyCategory(str, enum.Enum):
    """High-level category of a captured key event.

    Note: we store the *category*, never the literal character, by default.
    """

    LETTER = "LETTER"
    DIGIT = "DIGIT"
    WHITESPACE = "WHITESPACE"
    MODIFIER = "MODIFIER"
    ENTER = "ENTER"
    EDITING_KEY = "EDITING_KEY"
    NAVIGATION = "NAVIGATION"
    FUNCTION = "FUNCTION"
    PUNCTUATION = "PUNCTUATION"
    OTHER = "OTHER"


class SessionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    STOPPED = "STOPPED"


class Severity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SimulationStatus(str, enum.Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
