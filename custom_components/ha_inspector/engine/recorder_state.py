"""Typed recorder state model for HA Inspector."""

from __future__ import annotations

from dataclasses import dataclass

from .base_state import BaseState


@dataclass(slots=True)
class RecorderState(BaseState):
    """Represent the stable recorder information contract."""

    available: bool = False
    reason: str | None = None

    enabled: bool | None = None
    recording: bool | None = None
    is_running: bool | None = None
    auto_purge: bool | None = None
    auto_repack: bool | None = None

    keep_days: int | None = None
    commit_interval: int | float | None = None
    backlog: int | None = None
    schema_version: int | None = None

    migration_in_progress: bool | None = None
    migration_is_live: bool | None = None

    database_dialect: str | None = None
    database_connected: bool | None = None
    database_ready: bool | None = None
