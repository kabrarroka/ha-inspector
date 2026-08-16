"""Diagnostic sensors for HA Inspector."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DATA_LAST_RESULT,
    DOMAIN,
    NAME,
    SIGNAL_INSPECTION_FINISHED,
)


def status_from_summary(summary: dict[str, Any]) -> str:
    """Return the highest relevant severity represented in a summary."""
    if int(summary.get("critical", 0) or 0) > 0:
        return "critical"
    if int(summary.get("error", 0) or 0) > 0:
        return "error"
    if int(summary.get("warning", 0) or 0) > 0:
        return "warning"
    if int(summary.get("info", 0) or 0) > 0:
        return "info"
    return "ok"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HA Inspector diagnostic sensors."""
    async_add_entities([HAInspectorStatusSensor(hass, entry)])


class HAInspectorStatusSensor(SensorEntity):  # type: ignore[misc]
    """Expose the latest HA Inspector result."""

    _attr_has_entity_name = True
    _attr_name = "Status"
    _attr_icon = "mdi:home-search"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the status sensor."""
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": NAME,
            "manufacturer": "HA Inspector",
            "model": "Diagnostic engine",
        }

        result = hass.data.get(DOMAIN, {}).get(DATA_LAST_RESULT)
        self._update_from_result(result)

    @callback  # type: ignore[untyped-decorator]
    def _update_from_result(
        self,
        result: dict[str, Any] | None,
    ) -> None:
        """Update sensor state from an inspection result."""
        if not result:
            self._attr_native_value = "not_run"
            self._attr_extra_state_attributes = {
                "total_findings": 0,
                "score": None,
                "health_status": None,
                "checks_executed": 0,
                "finished_at": None,
                "duration_seconds": None,
            }
            return

        summary = result.get("summary", {})
        health = result.get("health", {})

        self._attr_native_value = status_from_summary(summary)
        self._attr_extra_state_attributes = {
            "score": result.get("score"),
            "health_status": health.get("status"),
            "total_findings": result.get("total_findings", 0),
            "checks_executed": result.get("checks_executed", 0),
            "finished_at": result.get("finished_at"),
            "duration_seconds": result.get("duration_seconds"),
            "info": summary.get("info", 0),
            "warnings": summary.get("warning", 0),
            "errors": summary.get("error", 0),
            "critical": summary.get("critical", 0),
            "categories": result.get("categories", {}),
            "health_summary": result.get("health_summary", {}),
        }

    async def async_added_to_hass(self) -> None:
        """Subscribe to completed inspections."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_INSPECTION_FINISHED,
                self._handle_inspection_finished,
            )
        )

    @callback  # type: ignore[untyped-decorator]
    def _handle_inspection_finished(
        self,
        result: dict[str, Any],
    ) -> None:
        """Handle a newly completed inspection."""
        self._update_from_result(result)
        self.async_write_ha_state()
