"""Typed storage state model for HA Inspector."""

from __future__ import annotations

from dataclasses import dataclass

from .base_state import BaseState


@dataclass(slots=True)
class StorageState(BaseState):
    """Represent the stable storage statistics contract."""

    total_bytes: int = 0
    used_bytes: int = 0
    free_bytes: int = 0
    free_percent: float = 0.0
