"""Tests for the HA Inspector status sensor."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from custom_components.ha_inspector.sensor import (
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
    assert len(entities) == 1
    assert isinstance(entities[0], HAInspectorStatusSensor)
    assert entities[0].unique_id == "entry-1_status"


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
