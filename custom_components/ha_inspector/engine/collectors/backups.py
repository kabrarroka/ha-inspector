"""Backup information collector for HA Inspector."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.backup.const import DATA_MANAGER

from ..context import InspectionContext
from .base import BaseCollector

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


def _build_backup_inventory_state() -> dict[str, Any]:
    """Return a fresh backup inventory state with the stable contract."""
    return {
        "available": False,
        "reason": None,
        "count": None,
        "latest": None,
        "oldest": None,
        "agent_error_count": 0,
        "agent_error_ids": [],
        "latest_backup_agent_count": None,
        "latest_backup_agent_ids": [],
        "latest_backup_failed_addons": [],
        "latest_backup_failed_folders": [],
        "latest_backup_failed_agent_ids": [],
    }


class BackupCollector(BaseCollector):
    """Collect backup inventory from Home Assistant's backup manager."""

    collector_id = "backups"

    async def collect(
        self,
        hass: HomeAssistant,
        context: InspectionContext,
    ) -> None:
        """Collect backup count and date boundaries."""
        manager = hass.data.get(DATA_MANAGER)

        if manager is None:
            state = _build_backup_inventory_state()
            state["reason"] = "Home Assistant backup manager is not available"
            context.backups.update(state)
            return

        try:
            backups, agent_errors = await manager.async_get_backups()
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("Unable to collect Home Assistant backups")
            state = _build_backup_inventory_state()
            state["reason"] = (
                "Backup inventory could not be read: "
                f"{type(err).__name__}"
            )
            context.backups.update(state)
            return

        dates = [
            backup.date
            for backup in backups.values()
            if isinstance(getattr(backup, "date", None), datetime)
        ]

        dated_backups = [
            backup
            for backup in backups.values()
            if isinstance(getattr(backup, "date", None), datetime)
        ]
        latest_backup = (
            max(dated_backups, key=lambda backup: backup.date)
            if dated_backups
            else None
        )
        latest_agents = getattr(latest_backup, "agents", None)
        latest_agent_ids = (
            sorted(str(agent_id) for agent_id in latest_agents)
            if isinstance(latest_agents, dict)
            else []
        )
        latest_failed_addons = sorted(
            {
                slug.strip()
                for addon in getattr(latest_backup, "failed_addons", [])
                if isinstance(
                    slug := getattr(addon, "slug", None),
                    str,
                )
                and slug.strip()
            }
        )
        latest_failed_folders = sorted(
            {
                str(getattr(folder, "value", folder)).strip()
                for folder in getattr(latest_backup, "failed_folders", [])
                if str(getattr(folder, "value", folder)).strip()
            }
        )
        latest_failed_agent_ids = sorted(
            {
                agent_id.strip()
                for agent_id in getattr(
                    latest_backup,
                    "failed_agent_ids",
                    [],
                )
                if isinstance(agent_id, str) and agent_id.strip()
            }
        )

        state = _build_backup_inventory_state()
        state.update(
            {
                "available": True,
                "count": len(backups),
                "latest": max(dates).isoformat() if dates else None,
                "oldest": min(dates).isoformat() if dates else None,
                "agent_error_count": len(agent_errors),
                "agent_error_ids": sorted(
                    str(agent_id)
                    for agent_id in agent_errors
                ),
                "latest_backup_agent_count": len(latest_agent_ids),
                "latest_backup_agent_ids": latest_agent_ids,
                "latest_backup_failed_addons": latest_failed_addons,
                "latest_backup_failed_folders": latest_failed_folders,
                "latest_backup_failed_agent_ids": latest_failed_agent_ids,
            }
        )
        context.backups.update(state)
