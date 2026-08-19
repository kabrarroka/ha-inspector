"""Typed system log state model for HA Inspector."""

from __future__ import annotations

from dataclasses import dataclass, field

from .base_state import BaseState


@dataclass(slots=True)
class LogsState(BaseState):
    """Represent recent Home Assistant system log health."""

    available: bool = False

    warning_entries: int = 0
    error_entries: int = 0
    critical_entries: int = 0

    warning_occurrences: int = 0
    error_occurrences: int = 0
    critical_occurrences: int = 0

    top_loggers: list[dict[str, object]] = field(default_factory=list)
