"""Tests for the HA Inspector status sensor."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from custom_components.ha_inspector.sensor import (
    HAInspectorCollectorFailuresSensor,
    HAInspectorDependencyHealthSensor,
    HAInspectorDependencyInvestigationSensor,
    HAInspectorDomainHealthSensor,
    HAInspectorFindingsSensor,
    HAInspectorHealthScoreSensor,
    HAInspectorStatusSensor,
    async_setup_entry,
    status_from_summary,
)


def test_status_from_summary() -> None:
    assert status_from_summary({"critical": 1}) == "critical"
    assert status_from_summary({"error": 1}) == "error"
    assert status_from_summary({"warning": 1}) == "warning"
    assert status_from_summary({"info": 1}) == "info"
    assert status_from_summary({}) == "ok"


def test_sensor_without_result() -> None:
    hass = SimpleNamespace(data={})
    entry = SimpleNamespace(entry_id="entry-1")

    sensor = HAInspectorStatusSensor(hass, entry)  # type: ignore[arg-type]

    assert sensor.native_value == "not_run"
    assert sensor.extra_state_attributes["total_findings"] == 0
    assert sensor.extra_state_attributes["score"] is None
    assert sensor.extra_state_attributes["domain_health"] == {}
    assert sensor.extra_state_attributes["suppressed_findings_count"] == 0
    assert sensor.extra_state_attributes["collectors_executed"] == 0
    assert sensor.extra_state_attributes["collectors_succeeded"] == 0
    assert sensor.extra_state_attributes["collectors_failed"] == 0
    assert sensor.extra_state_attributes["inspection_seconds"] is None
    assert sensor.extra_state_attributes["collectors_seconds"] is None
    assert sensor.extra_state_attributes["rules_seconds"] is None
    assert sensor.extra_state_attributes["diagnostics_included"] is False
    assert sensor.extra_state_attributes["language"] is None


def test_sensor_with_result() -> None:
    result: dict[str, Any] = {
        "summary": {
            "info": 1,
            "warning": 2,
            "error": 0,
            "critical": 0,
        },
        "score": 87,
        "health": {"status": "good"},
        "health_summary": {"good": 3},
        "dashboard_summary": {
            "status": "good",
            "score": 87,
            "total_findings": 3,
        },
        "domain_health": {
            "system": {
                "score": 100,
                "status": "excellent",
            },
        },
        "metadata": {
            "suppressed_findings_count": 2,
            "collectors_executed": 9,
            "collectors_succeeded": 8,
            "collectors_failed": 1,
            "diagnostics_included": True,
            "language": "es",
            "timings": {
                "inspection_seconds": 1.2,
                "collectors_seconds": 0.8,
                "rules_seconds": 0.4,
            },
        },
        "total_findings": 3,
        "checks_executed": 10,
        "finished_at": "2026-08-16T08:00:00+00:00",
        "duration_seconds": 1.5,
        "categories": {"system": {}},
    }

    hass = SimpleNamespace(
        data={"ha_inspector": {"last_result": result}}
    )
    entry = SimpleNamespace(entry_id="entry-1")

    sensor = HAInspectorStatusSensor(hass, entry)  # type: ignore[arg-type]

    assert sensor.native_value == "warning"
    assert sensor.extra_state_attributes["score"] == 87
    assert sensor.extra_state_attributes["health_status"] == "good"
    assert sensor.extra_state_attributes["warnings"] == 2
    assert sensor.extra_state_attributes["health_summary"] == {"good": 3}
    assert sensor.extra_state_attributes["dashboard_summary"] == {
        "status": "good",
        "score": 87,
        "total_findings": 3,
    }
    assert sensor.extra_state_attributes["domain_health"] == {
        "system": {
            "score": 100,
            "status": "excellent",
        },
    }
    assert sensor.extra_state_attributes["suppressed_findings_count"] == 2
    assert sensor.extra_state_attributes["collectors_executed"] == 9
    assert sensor.extra_state_attributes["collectors_succeeded"] == 8
    assert sensor.extra_state_attributes["collectors_failed"] == 1
    assert sensor.extra_state_attributes["inspection_seconds"] == 1.2
    assert sensor.extra_state_attributes["collectors_seconds"] == 0.8
    assert sensor.extra_state_attributes["rules_seconds"] == 0.4
    assert sensor.extra_state_attributes["diagnostics_included"] is True
    assert sensor.extra_state_attributes["language"] == "es"


def test_sensor_handles_finished_inspection() -> None:
    hass = SimpleNamespace(data={})
    entry = SimpleNamespace(entry_id="entry-1")

    sensor = HAInspectorStatusSensor(hass, entry)  # type: ignore[arg-type]

    sensor.async_write_ha_state = lambda: None  # type: ignore[method-assign]

    sensor._handle_inspection_finished(
        {
            "summary": {
                "critical": 1,
            },
            "score": 50,
            "health": {"status": "critical"},
            "total_findings": 1,
            "checks_executed": 2,
        }
    )

    assert sensor.native_value == "critical"
    assert sensor.extra_state_attributes["score"] == 50


@pytest.mark.asyncio
async def test_setup_entry_adds_status_sensor() -> None:
    hass = SimpleNamespace(data={})
    entry = SimpleNamespace(entry_id="entry-1")
    async_add_entities = MagicMock()

    await async_setup_entry(
        hass,  # type: ignore[arg-type]
        entry,  # type: ignore[arg-type]
        async_add_entities,
    )

    async_add_entities.assert_called_once()

    entities = async_add_entities.call_args.args[0]
    assert len(entities) == 10

    assert isinstance(entities[0], HAInspectorStatusSensor)
    assert entities[0].unique_id == "entry-1_status"

    assert isinstance(entities[1], HAInspectorHealthScoreSensor)
    assert entities[1].unique_id == "entry-1_health_score"

    assert isinstance(entities[2], HAInspectorFindingsSensor)
    assert entities[2].unique_id == "entry-1_findings"

    assert isinstance(entities[3], HAInspectorCollectorFailuresSensor)
    assert entities[3].unique_id == "entry-1_collector_failures"

    assert isinstance(entities[4], HAInspectorDependencyHealthSensor)
    assert entities[4].unique_id == "entry-1_dependency_health"

    assert isinstance(
        entities[5],
        HAInspectorDependencyInvestigationSensor,
    )
    assert entities[5].unique_id == "entry-1_dependency_investigation"

    expected_domains = (
        "storage",
        "system",
        "integrations",
        "entities",
    )

    for entity, domain in zip(entities[6:], expected_domains, strict=True):
        assert isinstance(entity, HAInspectorDomainHealthSensor)
        assert entity.unique_id == f"entry-1_{domain}_health"


@pytest.mark.asyncio
async def test_sensor_subscribes_when_added_to_hass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hass = SimpleNamespace(data={})
    entry = SimpleNamespace(entry_id="entry-1")

    sensor = HAInspectorStatusSensor(hass, entry)  # type: ignore[arg-type]
    sensor.hass = hass  # type: ignore[assignment]

    unsubscribe = MagicMock()
    connect = MagicMock(return_value=unsubscribe)
    on_remove = MagicMock()

    monkeypatch.setattr(
        "custom_components.ha_inspector.sensor.async_dispatcher_connect",
        connect,
    )
    sensor.async_on_remove = on_remove  # type: ignore[method-assign]

    await sensor.async_added_to_hass()

    connect.assert_called_once_with(
        hass,
        "ha_inspector_inspection_finished",
        sensor._handle_inspection_finished,
    )
    on_remove.assert_called_once_with(unsubscribe)

def test_diagnostic_sensors_without_result() -> None:
    hass = SimpleNamespace(data={})
    entry = SimpleNamespace(entry_id="entry-1")

    health = HAInspectorHealthScoreSensor(hass, entry)  # type: ignore[arg-type]
    findings = HAInspectorFindingsSensor(hass, entry)  # type: ignore[arg-type]
    collectors = HAInspectorCollectorFailuresSensor(  # type: ignore[arg-type]
        hass,
        entry,
    )

    assert health.native_value is None
    assert health.extra_state_attributes["health_status"] is None

    assert findings.native_value == 0
    assert findings.extra_state_attributes["critical"] == 0
    assert findings.extra_state_attributes["errors"] == 0
    assert findings.extra_state_attributes["warnings"] == 0
    assert findings.extra_state_attributes["info"] == 0

    assert collectors.native_value == 0
    assert collectors.extra_state_attributes["collectors_executed"] == 0
    assert collectors.extra_state_attributes["collectors_succeeded"] == 0
    assert collectors.extra_state_attributes["collector_errors"] == []


def test_diagnostic_sensors_with_result() -> None:
    result: dict[str, Any] = {
        "score": 72,
        "health": {"status": "fair"},
        "finished_at": "2026-08-25T08:00:00+00:00",
        "total_findings": 4,
        "summary": {
            "info": 1,
            "warning": 1,
            "error": 1,
            "critical": 1,
        },
        "metadata": {
            "collectors_executed": 9,
            "collectors_succeeded": 8,
            "collectors_failed": 1,
            "collector_errors": [
                {
                    "collector_id": "storage",
                    "error_type": "RuntimeError",
                    "message": "boom",
                }
            ],
        },
    }

    hass = SimpleNamespace(
        data={"ha_inspector": {"last_result": result}}
    )
    entry = SimpleNamespace(entry_id="entry-1")

    health = HAInspectorHealthScoreSensor(hass, entry)  # type: ignore[arg-type]
    findings = HAInspectorFindingsSensor(hass, entry)  # type: ignore[arg-type]
    collectors = HAInspectorCollectorFailuresSensor(  # type: ignore[arg-type]
        hass,
        entry,
    )

    assert health.native_value == 72
    assert health.extra_state_attributes["health_status"] == "fair"
    assert health.extra_state_attributes["finished_at"] == (
        "2026-08-25T08:00:00+00:00"
    )

    assert findings.native_value == 4
    assert findings.extra_state_attributes["critical"] == 1
    assert findings.extra_state_attributes["errors"] == 1
    assert findings.extra_state_attributes["warnings"] == 1
    assert findings.extra_state_attributes["info"] == 1

    assert collectors.native_value == 1
    assert collectors.extra_state_attributes["collectors_executed"] == 9
    assert collectors.extra_state_attributes["collectors_succeeded"] == 8
    assert collectors.extra_state_attributes["collector_errors"] == [
        {
            "collector_id": "storage",
            "error_type": "RuntimeError",
            "message": "boom",
        }
    ]


@pytest.mark.asyncio
async def test_diagnostic_sensor_subscription_and_update(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hass = SimpleNamespace(data={})
    entry = SimpleNamespace(entry_id="entry-1")

    sensor = HAInspectorHealthScoreSensor(  # type: ignore[arg-type]
        hass,
        entry,
    )
    sensor.hass = hass  # type: ignore[assignment]

    unsubscribe = MagicMock()
    connect = MagicMock(return_value=unsubscribe)
    on_remove = MagicMock()
    write_state = MagicMock()

    monkeypatch.setattr(
        "custom_components.ha_inspector.sensor.async_dispatcher_connect",
        connect,
    )
    sensor.async_on_remove = on_remove  # type: ignore[method-assign]
    sensor.async_write_ha_state = write_state  # type: ignore[method-assign]

    await sensor.async_added_to_hass()

    connect.assert_called_once_with(
        hass,
        "ha_inspector_inspection_finished",
        sensor._handle_inspection_finished,
    )
    on_remove.assert_called_once_with(unsubscribe)

    sensor._handle_inspection_finished(
        {
            "score": 91,
            "health": {"status": "excellent"},
            "finished_at": "2026-08-25T08:00:00+00:00",
        }
    )

    assert sensor.native_value == 91
    assert sensor.extra_state_attributes["health_status"] == "excellent"
    write_state.assert_called_once()


def test_diagnostic_sensor_base_requires_update_implementation() -> None:
    from custom_components.ha_inspector.sensor import (
        HAInspectorDiagnosticSensor,
    )

    hass = SimpleNamespace(data={})
    entry = SimpleNamespace(entry_id="entry-1")

    with pytest.raises(NotImplementedError):
        HAInspectorDiagnosticSensor(  # type: ignore[arg-type]
            hass,
            entry,
            key="test",
        )

def test_domain_health_sensor_without_result() -> None:
    hass = SimpleNamespace(data={})
    entry = SimpleNamespace(entry_id="entry-1")

    sensor = HAInspectorDomainHealthSensor(  # type: ignore[arg-type]
        hass,
        entry,
        domain="storage",
    )

    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {
        "status": "not_checked",
        "health_status": None,
        "max_score": None,
        "penalty": None,
        "checks": 0,
        "findings": 0,
    }


def test_domain_health_sensor_with_checked_result() -> None:
    result: dict[str, Any] = {
        "domain_health": {
            "storage": {
                "domain": "storage",
                "status": "checked",
                "health": {
                    "score": 94,
                    "max_score": 100,
                    "status": "excellent",
                    "penalty": 6.0,
                },
                "checks": 2,
                "findings": 1,
            },
        },
    }

    hass = SimpleNamespace(
        data={"ha_inspector": {"last_result": result}}
    )
    entry = SimpleNamespace(entry_id="entry-1")

    sensor = HAInspectorDomainHealthSensor(  # type: ignore[arg-type]
        hass,
        entry,
        domain="storage",
    )

    assert sensor.native_value == 94
    assert sensor.extra_state_attributes == {
        "status": "checked",
        "health_status": "excellent",
        "max_score": 100,
        "penalty": 6.0,
        "checks": 2,
        "findings": 1,
    }


def test_domain_health_sensor_with_not_checked_result() -> None:
    result: dict[str, Any] = {
        "domain_health": {
            "system": {
                "domain": "system",
                "status": "not_checked",
                "health": None,
                "checks": 0,
                "findings": 0,
            },
        },
    }

    hass = SimpleNamespace(
        data={"ha_inspector": {"last_result": result}}
    )
    entry = SimpleNamespace(entry_id="entry-1")

    sensor = HAInspectorDomainHealthSensor(  # type: ignore[arg-type]
        hass,
        entry,
        domain="system",
    )

    assert sensor.native_value is None
    assert sensor.extra_state_attributes["status"] == "not_checked"
    assert sensor.extra_state_attributes["checks"] == 0
    assert sensor.extra_state_attributes["findings"] == 0


def test_domain_health_sensor_handles_invalid_domain_data() -> None:
    entry = SimpleNamespace(entry_id="entry-1")

    hass = SimpleNamespace(
        data={
            "ha_inspector": {
                "last_result": {
                    "domain_health": {
                        "entities": "invalid",
                    },
                }
            }
        }
    )

    sensor = HAInspectorDomainHealthSensor(  # type: ignore[arg-type]
        hass,
        entry,
        domain="entities",
    )

    assert sensor.native_value is None
    assert sensor.extra_state_attributes["status"] == "not_checked"

    hass = SimpleNamespace(
        data={
            "ha_inspector": {
                "last_result": {
                    "domain_health": {
                        "integrations": {
                            "domain": "integrations",
                            "status": "checked",
                            "health": None,
                            "checks": 3,
                            "findings": 2,
                        },
                    },
                }
            }
        }
    )

    sensor = HAInspectorDomainHealthSensor(  # type: ignore[arg-type]
        hass,
        entry,
        domain="integrations",
    )

    assert sensor.native_value is None
    assert sensor.extra_state_attributes["status"] == "not_checked"
    assert sensor.extra_state_attributes["checks"] == 3
    assert sensor.extra_state_attributes["findings"] == 2


def test_dependency_health_sensor_without_result() -> None:
    """Dependency health sensor exposes a stable empty state."""
    hass = SimpleNamespace(data={})
    entry = SimpleNamespace(entry_id="entry-1")

    sensor = HAInspectorDependencyHealthSensor(  # type: ignore[arg-type]
        hass,
        entry,
    )

    assert sensor.native_value == 0
    assert sensor.extra_state_attributes == {
        "unavailable": 0,
        "unknown": 0,
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "max_impact_score": 0,
    }


def test_dependency_health_sensor_with_result() -> None:
    """Dependency health sensor exposes compact dependency diagnostics."""
    result: dict[str, Any] = {
        "dashboard_summary": {
            "dependencies": {
                "affected_entities": 4,
                "unavailable": 2,
                "unknown": 2,
                "critical": 1,
                "high": 1,
                "medium": 1,
                "low": 1,
                "max_impact_score": 55,
            },
        },
    }

    hass = SimpleNamespace(
        data={"ha_inspector": {"last_result": result}}
    )
    entry = SimpleNamespace(entry_id="entry-1")

    sensor = HAInspectorDependencyHealthSensor(  # type: ignore[arg-type]
        hass,
        entry,
    )

    assert sensor.native_value == 4
    assert sensor.extra_state_attributes == {
        "unavailable": 2,
        "unknown": 2,
        "critical": 1,
        "high": 1,
        "medium": 1,
        "low": 1,
        "max_impact_score": 55,
    }


def test_dependency_health_sensor_handles_invalid_summary() -> None:
    """Dependency health sensor tolerates malformed result data."""
    hass = SimpleNamespace(
        data={
            "ha_inspector": {
                "last_result": {
                    "dashboard_summary": {
                        "dependencies": "invalid",
                    },
                },
            },
        }
    )
    entry = SimpleNamespace(entry_id="entry-1")

    sensor = HAInspectorDependencyHealthSensor(  # type: ignore[arg-type]
        hass,
        entry,
    )

    assert sensor.native_value == 0
    assert sensor.extra_state_attributes["max_impact_score"] == 0


def test_dependency_investigation_sensor_without_result() -> None:
    """Dependency investigation sensor exposes a stable empty state."""
    hass = SimpleNamespace(data={})
    entry = SimpleNamespace(entry_id="entry-1")

    sensor = HAInspectorDependencyInvestigationSensor(  # type: ignore[arg-type]
        hass,
        entry,
    )

    assert sensor.native_value == 0
    assert sensor.extra_state_attributes == {
        "missing_entities": [],
        "unreferenced_entity_count": 0,
        "unreferenced_entities": [],
        "disabled_automation_count": 0,
    }


def test_dependency_investigation_sensor_with_result() -> None:
    """Dependency investigation sensor exposes entity investigation data."""
    result: dict[str, Any] = {
        "diagnostics": {
            "entities": {
                "missing_entity_count": 2,
                "missing_entities": [
                    "sensor.removed_temperature",
                    "switch.removed_pump",
                ],
                "unreferenced_entity_count": 1,
                "unreferenced_entities": [
                    {
                        "entity_id": "sensor.unused",
                        "name": "Unused",
                        "domain": "sensor",
                    },
                ],
                "disabled_automation_count": 3,
            },
        },
    }

    hass = SimpleNamespace(
        data={"ha_inspector": {"last_result": result}}
    )
    entry = SimpleNamespace(entry_id="entry-1")

    sensor = HAInspectorDependencyInvestigationSensor(  # type: ignore[arg-type]
        hass,
        entry,
    )

    assert sensor.native_value == 2
    assert sensor.extra_state_attributes == {
        "missing_entities": [
            "sensor.removed_temperature",
            "switch.removed_pump",
        ],
        "unreferenced_entity_count": 1,
        "unreferenced_entities": [
            {
                "entity_id": "sensor.unused",
                "name": "Unused",
                "domain": "sensor",
            },
        ],
        "disabled_automation_count": 3,
    }


def test_dependency_investigation_sensor_handles_invalid_diagnostics() -> None:
    """Dependency investigation sensor tolerates malformed diagnostics."""
    hass = SimpleNamespace(
        data={
            "ha_inspector": {
                "last_result": {
                    "diagnostics": {
                        "entities": "invalid",
                    },
                },
            }
        }
    )
    entry = SimpleNamespace(entry_id="entry-1")

    sensor = HAInspectorDependencyInvestigationSensor(  # type: ignore[arg-type]
        hass,
        entry,
    )

    assert sensor.native_value == 0
    assert sensor.extra_state_attributes == {
        "missing_entities": [],
        "unreferenced_entity_count": 0,
        "unreferenced_entities": [],
        "disabled_automation_count": 0,
    }
