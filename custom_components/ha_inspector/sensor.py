"""Diagnostic sensors for HA Inspector."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory
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
    async_add_entities(
        [
            HAInspectorStatusSensor(hass, entry),
            HAInspectorHealthScoreSensor(hass, entry),
            HAInspectorFindingsSensor(hass, entry),
            HAInspectorCollectorFailuresSensor(hass, entry),
            HAInspectorDependencyHealthSensor(hass, entry),
            HAInspectorDomainHealthSensor(hass, entry, domain="storage"),
            HAInspectorDomainHealthSensor(hass, entry, domain="system"),
            HAInspectorDomainHealthSensor(
                hass,
                entry,
                domain="integrations",
            ),
            HAInspectorDomainHealthSensor(hass, entry, domain="entities"),
        ]
    )


class HAInspectorStatusSensor(SensorEntity):  # type: ignore[misc]
    """Expose the latest HA Inspector result."""

    _attr_has_entity_name = True
    _attr_name = "Status"
    _attr_icon = "mdi:home-search"
    _attr_extra_state_attributes: dict[str, Any]

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
                "info": 0,
                "warnings": 0,
                "errors": 0,
                "critical": 0,
                "categories": {},
                "health_summary": {},
                "domain_health": {},
                "dashboard_summary": None,
                "suppressed_findings_count": 0,
                "collectors_executed": 0,
                "collectors_succeeded": 0,
                "collectors_failed": 0,
                "inspection_seconds": None,
                "collectors_seconds": None,
                "rules_seconds": None,
                "diagnostics_included": False,
                "language": None,
            }
            return

        summary = result.get("summary", {})
        health = result.get("health", {})
        metadata = result.get("metadata", {})
        timings = metadata.get("timings", {})

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
            "domain_health": result.get("domain_health", {}),
            "dashboard_summary": result.get("dashboard_summary", {}),
            "suppressed_findings_count": metadata.get(
                "suppressed_findings_count", 0
            ),
            "collectors_executed": metadata.get("collectors_executed", 0),
            "collectors_succeeded": metadata.get("collectors_succeeded", 0),
            "collectors_failed": metadata.get("collectors_failed", 0),
            "inspection_seconds": timings.get("inspection_seconds"),
            "collectors_seconds": timings.get("collectors_seconds"),
            "rules_seconds": timings.get("rules_seconds"),
            "diagnostics_included": metadata.get(
                "diagnostics_included", False
            ),
            "language": metadata.get("language"),
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

class HAInspectorDiagnosticSensor(SensorEntity):  # type: ignore[misc]
    """Base class for HA Inspector diagnostic sensors."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        *,
        key: str,
    ) -> None:
        """Initialize a diagnostic sensor."""
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": NAME,
            "manufacturer": "HA Inspector",
            "model": "Diagnostic engine",
        }

        result = hass.data.get(DOMAIN, {}).get(DATA_LAST_RESULT)
        self._update_from_result(result)

    def _update_from_result(
        self,
        result: dict[str, Any] | None,
    ) -> None:
        """Update entity from an inspection result."""
        raise NotImplementedError

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


class HAInspectorHealthScoreSensor(HAInspectorDiagnosticSensor):
    """Expose the latest HA Inspector health score."""

    _attr_name = "Health score"
    _attr_icon = "mdi:heart-pulse"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the health score sensor."""
        super().__init__(hass, entry, key="health_score")

    def _update_from_result(
        self,
        result: dict[str, Any] | None,
    ) -> None:
        """Update health score from the latest inspection."""
        if not result:
            self._attr_native_value = None
            self._attr_extra_state_attributes = {
                "health_status": None,
                "finished_at": None,
            }
            return

        health = result.get("health", {})
        self._attr_native_value = result.get("score")
        self._attr_extra_state_attributes = {
            "health_status": health.get("status"),
            "finished_at": result.get("finished_at"),
        }


class HAInspectorFindingsSensor(HAInspectorDiagnosticSensor):
    """Expose the latest HA Inspector finding count."""

    _attr_name = "Findings"
    _attr_icon = "mdi:alert-circle-outline"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the findings sensor."""
        super().__init__(hass, entry, key="findings")

    def _update_from_result(
        self,
        result: dict[str, Any] | None,
    ) -> None:
        """Update finding count from the latest inspection."""
        if not result:
            self._attr_native_value = 0
            self._attr_extra_state_attributes = {
                "info": 0,
                "warnings": 0,
                "errors": 0,
                "critical": 0,
            }
            return

        summary = result.get("summary", {})
        self._attr_native_value = result.get("total_findings", 0)
        self._attr_extra_state_attributes = {
            "info": summary.get("info", 0),
            "warnings": summary.get("warning", 0),
            "errors": summary.get("error", 0),
            "critical": summary.get("critical", 0),
        }


class HAInspectorCollectorFailuresSensor(HAInspectorDiagnosticSensor):
    """Expose collector failure diagnostics."""

    _attr_name = "Collector failures"
    _attr_icon = "mdi:database-alert-outline"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the collector failures sensor."""
        super().__init__(hass, entry, key="collector_failures")

    def _update_from_result(
        self,
        result: dict[str, Any] | None,
    ) -> None:
        """Update collector failure diagnostics."""
        if not result:
            self._attr_native_value = 0
            self._attr_extra_state_attributes = {
                "collectors_executed": 0,
                "collectors_succeeded": 0,
                "collector_errors": [],
            }
            return

        metadata = result.get("metadata", {})
        self._attr_native_value = metadata.get("collectors_failed", 0)
        self._attr_extra_state_attributes = {
            "collectors_executed": metadata.get("collectors_executed", 0),
            "collectors_succeeded": metadata.get("collectors_succeeded", 0),
            "collector_errors": metadata.get("collector_errors", []),
        }

class HAInspectorDependencyHealthSensor(HAInspectorDiagnosticSensor):
    """Expose dependency health diagnostics."""

    _attr_name = "Dependency health"
    _attr_icon = "mdi:vector-link"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the dependency health sensor."""
        super().__init__(hass, entry, key="dependency_health")

    def _update_from_result(
        self,
        result: dict[str, Any] | None,
    ) -> None:
        """Update dependency health from the latest inspection."""
        dependencies: dict[str, Any] = {}

        if result:
            dashboard_summary = result.get("dashboard_summary", {})
            if isinstance(dashboard_summary, dict):
                candidate = dashboard_summary.get("dependencies", {})
                if isinstance(candidate, dict):
                    dependencies = candidate

        self._attr_native_value = dependencies.get("affected_entities", 0)
        self._attr_extra_state_attributes = {
            "unavailable": dependencies.get("unavailable", 0),
            "unknown": dependencies.get("unknown", 0),
            "critical": dependencies.get("critical", 0),
            "high": dependencies.get("high", 0),
            "medium": dependencies.get("medium", 0),
            "low": dependencies.get("low", 0),
            "max_impact_score": dependencies.get("max_impact_score", 0),
        }


class HAInspectorDomainHealthSensor(HAInspectorDiagnosticSensor):
    """Expose health information for a primary HA Inspector domain."""

    _attr_icon = "mdi:chart-donut"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        *,
        domain: str,
    ) -> None:
        """Initialize a domain health sensor."""
        self._domain = domain
        self._attr_name = f"{domain.capitalize()} health"
        super().__init__(
            hass,
            entry,
            key=f"{domain}_health",
        )

    def _update_from_result(
        self,
        result: dict[str, Any] | None,
    ) -> None:
        """Update domain health from the latest inspection."""
        if not result:
            self._set_not_checked()
            return

        domain_health = result.get("domain_health", {})
        domain_data = domain_health.get(self._domain)

        if (
            not isinstance(domain_data, dict)
            or domain_data.get("status") != "checked"
        ):
            self._set_not_checked(
                checks=(
                    domain_data.get("checks", 0)
                    if isinstance(domain_data, dict)
                    else 0
                ),
                findings=(
                    domain_data.get("findings", 0)
                    if isinstance(domain_data, dict)
                    else 0
                ),
            )
            return

        health = domain_data.get("health")

        if not isinstance(health, dict):
            self._set_not_checked(
                checks=domain_data.get("checks", 0),
                findings=domain_data.get("findings", 0),
            )
            return

        self._attr_native_value = health.get("score")
        self._attr_extra_state_attributes = {
            "status": "checked",
            "health_status": health.get("status"),
            "max_score": health.get("max_score"),
            "penalty": health.get("penalty"),
            "checks": domain_data.get("checks", 0),
            "findings": domain_data.get("findings", 0),
        }

    def _set_not_checked(
        self,
        *,
        checks: int = 0,
        findings: int = 0,
    ) -> None:
        """Set a stable not-checked state."""
        self._attr_native_value = None
        self._attr_extra_state_attributes = {
            "status": "not_checked",
            "health_status": None,
            "max_score": None,
            "penalty": None,
            "checks": checks,
            "findings": findings,
        }
