"""Severity levels for HA Inspector rule results."""

from __future__ import annotations

from enum import StrEnum


class Severity(StrEnum):
    """Represent the severity of a rule result."""

    OK = "ok"
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    ERROR = "error"
