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
            context.backups.update(
                {
                    "available": False,
                    "reason": "Home Assistant backup manager is not available",
                    "count": None,
                    "latest": None,
                    "oldest": None,
                    "agent_error_count": 0,
                    "agent_error_ids": [],
                }
            )
            return

        try:
            backups, agent_errors = await manager.async_get_backups()
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("Unable to collect Home Assistant backups")
            context.backups.update(
                {
                    "available": False,
                    "reason": (
                        "Backup inventory could not be read: "
                        f"{type(err).__name__}"
                    ),
                    "count": None,
                    "latest": None,
                    "oldest": None,
                    "agent_error_count": 0,
                    "agent_error_ids": [],
                }
            )
            return

        dates = [
            backup.date
            for backup in backups.values()
            if isinstance(getattr(backup, "date", None), datetime)
        ]

        context.backups.update(
            {
                "available": True,
                "reason": None,
                "count": len(backups),
                "latest": max(dates).isoformat() if dates else None,
                "oldest": min(dates).isoformat() if dates else None,
                "agent_error_count": len(agent_errors),
                "agent_error_ids": sorted(
                    str(agent_id)
                    for agent_id in agent_errors
                ),
            }
        )
