"""Storage collector for HA Inspector."""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

from ..context import InspectionContext
from .base import BaseCollector

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class StorageCollector(BaseCollector):
    """Collect storage statistics for the Home Assistant config partition."""

    collector_id = "storage"

    async def collect(
        self,
        hass: HomeAssistant,
        context: InspectionContext,
    ) -> None:
        """Collect storage totals without exposing filesystem paths."""
        usage = await hass.async_add_executor_job(
            shutil.disk_usage,
            hass.config.path(),
        )

        free_percent = (
            round((usage.free / usage.total) * 100, 2)
            if usage.total
            else 0.0
        )

        context.storage.update(
            {
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
                "free_percent": free_percent,
            }
        )
