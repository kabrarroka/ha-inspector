"""Config entry collector for HA Inspector."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Any

from ..context import InspectionContext
from .base import BaseCollector

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class IntegrationsCollector(BaseCollector):
    """Collect information about Home Assistant config entries."""

    collector_id = "integrations"

    async def collect(
        self,
        hass: HomeAssistant,
        context: InspectionContext,
    ) -> None:
        """Collect config entry states without exposing private entry data."""
        entries = hass.config_entries.async_entries()

        states = Counter(entry.state.value for entry in entries)
        domains = Counter(entry.domain for entry in entries)

        problematic_entries: list[dict[str, Any]] = []

        problematic_states = {
            "setup_error",
            "setup_retry",
            "migration_error",
            "failed_unload",
        }

        for entry in entries:
            state = entry.state.value

            if state not in problematic_states:
                continue

            problematic_entries.append(
                {
                    "domain": entry.domain,
                    "title": entry.title,
                    "state": state,
                    "reason": entry.reason,
                }
            )

        context.integrations.update(
            {
                "total_entries": len(entries),
                "states": dict(sorted(states.items())),
                "domains": dict(sorted(domains.items())),
                "problematic_entries": problematic_entries,
                "problematic_count": len(problematic_entries),
            }
        )