"""Typed system state model for HA Inspector."""

from __future__ import annotations

from dataclasses import dataclass

from .base_state import BaseState


@dataclass(slots=True)
class SystemState(BaseState):
    """Represent the stable system information contract."""

    home_assistant_version: str = ""
    python_version: str = ""
    python_implementation: str = ""
    architecture: str = ""
    platform: str = ""
    platform_release: str = ""

    timezone: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    elevation: int | float | None = None
    currency: str | None = None
    country: str | None = None
    language: str | None = None

    config_directory: str = ""
    internal_url: str | None = None
    external_url: str | None = None
    python_executable: str = ""

    cpu_percent: float | None = None
    cpu_count_logical: int | None = None
    cpu_count_physical: int | None = None
    load_1m: float | None = None
    load_5m: float | None = None
    load_15m: float | None = None

    memory_total_bytes: int | None = None
    memory_available_bytes: int | None = None
    memory_used_bytes: int | None = None
    memory_percent: float | None = None

    restart_count_24h: int | None = None
    restart_count_7d: int | None = None
