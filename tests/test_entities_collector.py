"""Tests for the entities collector."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN

from custom_components.ha_inspector.engine.collectors import entities as entities_module
from custom_components.ha_inspector.engine.collectors.entities import EntitiesCollector
from custom_components.ha_inspector.engine.context import InspectionContext


class FakeState:
    def __init__(
        self,
        entity_id: str,
        state: str,
        name: str,
    ) -> None:
        self.entity_id = entity_id
        self.state = state
        self.name = name
        self.domain = entity_id.split(".", 1)[0]


class FakeStates:
    def __init__(self, states: list[FakeState]) -> None:
        self._states = states

    def async_all(self) -> list[FakeState]:
        return self._states

    def get(self, entity_id: str) -> FakeState | None:
        return next(
            (
                state
                for state in self._states
                if state.entity_id == entity_id
            ),
            None,
        )

class FakeDeviceRegistry:
    def __init__(self, devices: dict[str, SimpleNamespace] | None = None) -> None:
        self._devices = devices or {}

    def async_get(self, device_id: str) -> SimpleNamespace | None:
        return self._devices.get(device_id)


class FakeHass:
    def __init__(self, states: list[FakeState]) -> None:
        self.states = FakeStates(states)


@pytest.mark.asyncio
async def test_collect_empty_entities(monkeypatch) -> None:
    registry = SimpleNamespace(entities={})

    monkeypatch.setattr(
        entities_module.er,
        "async_get",
        lambda hass: registry,
    )

    monkeypatch.setattr(
        entities_module.dr,
        "async_get",
        lambda hass: FakeDeviceRegistry(),
    )

    context = InspectionContext()

    await EntitiesCollector().collect(
        FakeHass([]),
        context,
    )

    assert context.entities.as_dict() == {
        "total_entities": 0,
        "domain_counts": {},
        "unavailable_count": 0,
        "unknown_count": 0,
        "unavailable_domains": {},
        "unknown_domains": {},
        "unavailable_entities": [],
        "unknown_entities": [],
        "duplicate_name_count": 0,
        "duplicate_names": [],
        "disabled_automation_count": 0,
        "disabled_automations": [],
        "unassigned_area_count": 0,
        "unassigned_area_entities": [],
    }


@pytest.mark.asyncio
async def test_collect_entity_statistics_and_duplicates(monkeypatch) -> None:
    registry = SimpleNamespace(entities={})

    monkeypatch.setattr(
        entities_module.er,
        "async_get",
        lambda hass: registry,
    )

    monkeypatch.setattr(
        entities_module.dr,
        "async_get",
        lambda hass: FakeDeviceRegistry(),
    )

    states = [
        FakeState(
            "sensor.kitchen_temperature",
            STATE_UNAVAILABLE,
            "Temperature",
        ),
        FakeState(
            "sensor.living_room_temperature",
            STATE_UNKNOWN,
            " temperature ",
        ),
        FakeState(
            "light.kitchen",
            "on",
            "Kitchen",
        ),
        FakeState(
            "sensor.unnamed",
            "10",
            "   ",
        ),
    ]

    context = InspectionContext()

    await EntitiesCollector().collect(
        FakeHass(states),
        context,
    )

    entities = context.entities

    assert entities.total_entities == 4
    assert entities.domain_counts == {
        "light": 1,
        "sensor": 3,
    }

    assert entities.unavailable_count == 1
    assert entities.unavailable_domains == {"sensor": 1}
    assert entities.unavailable_entities[0].entity_id == (
        "sensor.kitchen_temperature"
    )

    assert entities.unknown_count == 1
    assert entities.unknown_domains == {"sensor": 1}
    assert entities.unknown_entities[0].entity_id == (
        "sensor.living_room_temperature"
    )

    assert entities.duplicate_name_count == 1

    duplicate = entities.duplicate_names[0]

    assert duplicate.name == "Temperature"
    assert duplicate.entity_ids == [
        "sensor.kitchen_temperature",
        "sensor.living_room_temperature",
    ]
    assert duplicate.count == 2


@pytest.mark.asyncio
async def test_collect_disabled_automations(monkeypatch) -> None:
    registry = SimpleNamespace(
        entities={
            "1": SimpleNamespace(
                entity_id="automation.z_rule",
                domain="automation",
                name=None,
                original_name="Z rule",
                disabled_by=SimpleNamespace(value="user"),
                entity_category=None,
                area_id=None,
                device_id=None,
            ),
            "2": SimpleNamespace(
                entity_id="automation.a_rule",
                domain="automation",
                name="A rule",
                original_name=None,
                disabled_by="integration",
                entity_category=None,
                area_id=None,
                device_id=None,
            ),
            "3": SimpleNamespace(
                entity_id="automation.enabled",
                domain="automation",
                name="Enabled",
                original_name=None,
                disabled_by=None,
                entity_category=None,
                area_id=None,
                device_id=None,
            ),
            "4": SimpleNamespace(
                entity_id="sensor.disabled",
                domain="sensor",
                name="Sensor",
                original_name=None,
                disabled_by="user",
                entity_category=None,
                area_id=None,
                device_id=None,
            ),
        }
    )

    monkeypatch.setattr(
        entities_module.er,
        "async_get",
        lambda hass: registry,
    )

    monkeypatch.setattr(
        entities_module.dr,
        "async_get",
        lambda hass: FakeDeviceRegistry(),
    )

    context = InspectionContext()

    await EntitiesCollector().collect(
        FakeHass([]),
        context,
    )

    assert context.entities.disabled_automation_count == 2

    assert [
        automation.entity_id
        for automation in context.entities.disabled_automations
    ] == [
        "automation.a_rule",
        "automation.z_rule",
    ]

    assert context.entities.disabled_automations[0].name == "A rule"
    assert context.entities.disabled_automations[0].disabled_by == "integration"

    assert context.entities.disabled_automations[1].name == "Z rule"
    assert context.entities.disabled_automations[1].disabled_by == "user"

@pytest.mark.asyncio
async def test_collect_unassigned_area_entities(monkeypatch) -> None:
    registry = SimpleNamespace(
        entities={
            "1": SimpleNamespace(
                entity_id="sensor.direct_area",
                domain="sensor",
                name="Direct area",
                original_name=None,
                disabled_by=None,
                entity_category=None,
                area_id="kitchen",
                device_id=None,
            ),
            "2": SimpleNamespace(
                entity_id="sensor.device_area",
                domain="sensor",
                name="Device area",
                original_name=None,
                disabled_by=None,
                entity_category=None,
                area_id=None,
                device_id="device-1",
            ),
            "3": SimpleNamespace(
                entity_id="sensor.no_area",
                domain="sensor",
                name="No area",
                original_name=None,
                disabled_by=None,
                entity_category=None,
                area_id=None,
                device_id=None,
            ),
            "4": SimpleNamespace(
                entity_id="sensor.diagnostic",
                domain="sensor",
                name="Diagnostic",
                original_name=None,
                disabled_by=None,
                entity_category="diagnostic",
                area_id=None,
                device_id=None,
            ),
        }
    )

    monkeypatch.setattr(
        entities_module.er,
        "async_get",
        lambda hass: registry,
    )

    monkeypatch.setattr(
        entities_module.dr,
        "async_get",
        lambda hass: FakeDeviceRegistry(
            {
                "device-1": SimpleNamespace(
                    area_id="living_room",
                )
            }
        ),
    )

    states = [
        FakeState(
            "sensor.direct_area",
            "10",
            "Direct area",
        ),
        FakeState(
            "sensor.device_area",
            "20",
            "Device area",
        ),
        FakeState(
            "sensor.no_area",
            "30",
            "No area",
        ),
        FakeState(
            "sensor.diagnostic",
            "40",
            "Diagnostic",
        ),
    ]

    context = InspectionContext()

    await EntitiesCollector().collect(
        FakeHass(states),
        context,
    )

    assert context.entities.unassigned_area_count == 1

    assert [
        entity.entity_id
        for entity in context.entities.unassigned_area_entities
    ] == [
        "sensor.no_area",
    ]

    entity = context.entities.unassigned_area_entities[0]

    assert entity.name == "No area"
    assert entity.domain == "sensor"