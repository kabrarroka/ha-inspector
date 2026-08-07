"""Typed backup state model for HA Inspector."""

from __future__ import annotations

from dataclasses import dataclass, field

from .base_state import BaseState


@dataclass(slots=True)
class BackupState(BaseState):
    """Represent the stable backup inventory contract."""

    available: bool = False
    reason: str | None = None
    count: int | None = None
    latest: str | None = None
    oldest: str | None = None

    agent_error_count: int = 0
    agent_error_ids: list[str] = field(default_factory=list)

    latest_backup_agent_count: int | None = None
    latest_backup_agent_ids: list[str] = field(default_factory=list)

    latest_backup_failed_addons: list[str] = field(default_factory=list)
    latest_backup_failed_folders: list[str] = field(default_factory=list)
    latest_backup_failed_agent_ids: list[str] = field(default_factory=list)