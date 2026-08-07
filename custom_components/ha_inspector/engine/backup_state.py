"""Typed backup state model for HA Inspector."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class BackupState:
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

    def as_dict(self) -> dict[str, Any]:
        """Return the current backup state using the public dictionary contract."""
        return {
            "available": self.available,
            "reason": self.reason,
            "count": self.count,
            "latest": self.latest,
            "oldest": self.oldest,
            "agent_error_count": self.agent_error_count,
            "agent_error_ids": list(self.agent_error_ids),
            "latest_backup_agent_count": self.latest_backup_agent_count,
            "latest_backup_agent_ids": list(self.latest_backup_agent_ids),
            "latest_backup_failed_addons": list(
                self.latest_backup_failed_addons
            ),
            "latest_backup_failed_folders": list(
                self.latest_backup_failed_folders
            ),
            "latest_backup_failed_agent_ids": list(
                self.latest_backup_failed_agent_ids
            ),
        }