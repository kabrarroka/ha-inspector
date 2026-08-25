"""Typed Repairs issue state for HA Inspector."""

from __future__ import annotations

from dataclasses import dataclass, field

from .base_state import BaseState


@dataclass(slots=True)
class RepairsState(BaseState):
    """Represent active Home Assistant Repairs issues."""

    available: bool = False
    total: int = 0

    critical: int = 0
    error: int = 0
    warning: int = 0

    fixable: int = 0
    breaking: int = 0
    learn_more: int = 0
    issues: list[dict[str, object]] = field(default_factory=list)
