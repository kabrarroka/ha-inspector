"""Typed add-on health state for HA Inspector."""

from __future__ import annotations

from dataclasses import dataclass, field

from .base_state import BaseState


@dataclass(slots=True)
class AddonsState(BaseState):
    """Represent Home Assistant Supervisor add-on health."""

    available: bool = False
    total: int = 0

    started: int = 0
    startup: int = 0
    stopped: int = 0
    unknown: int = 0
    error: int = 0

    problematic: list[dict[str, str]] = field(default_factory=list)
    updates_available: list[dict[str, str]] = field(default_factory=list)
