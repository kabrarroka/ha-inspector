"""Tests for the HA Inspector status sensor."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from custom_components.ha_inspector.sensor import (
    HAInspectorCollectorFailuresSensor,
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
    assert len(entities) == 4

    assert isinstance(entities[0], HAInspectorStatusSensor)
    assert entities[0].unique_id == "entry-1_status"

    assert isinstance(entities[1], HAInspectorHealthScoreSensor)
    assert entities[1].unique_id == "entry-1_health_score"

    assert isinstance(entities[2], HAInspectorFindingsSensor)
    assert entities[2].unique_id == "entry-1_findings"

    assert isinstance(entities[3], HAInspectorCollectorFailuresSensor)
    assert entities[3].unique_id == "entry-1_collector_failures"


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
