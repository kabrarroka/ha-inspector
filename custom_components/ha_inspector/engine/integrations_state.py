"""Typed integrations state model for HA Inspector."""

from __future__ import annotations

from dataclasses import dataclass, field

from .base_state import BaseState


@dataclass(slots=True)
class ProblematicIntegrationEntry:
    """Represent a config entry in a problematic state."""

    domain: str
    title: str
    state: str
    reason: str | None = None


@dataclass(slots=True)
class IntegrationsState(BaseState):
    """Represent the stable integrations inspection contract."""

    total_entries: int = 0
    states: dict[str, int] = field(default_factory=dict)
    domains: dict[str, int] = field(default_factory=dict)
    problematic_entries: list[ProblematicIntegrationEntry] = field(
        default_factory=list
    )
    problematic_count: int = 0
