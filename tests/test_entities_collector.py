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


@pytest.fixture(autouse=True)
def mock_entities_in_automation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Isolate collector tests from Home Assistant automation internals."""
    monkeypatch.setattr(
        entities_module,
        "entities_in_automation",
        lambda hass, entity_id: [],
    )
    monkeypatch.setattr(
        entities_module,
        "entities_in_script",
        lambda hass, entity_id: [],
    )
    monkeypatch.setattr(
        entities_module,
        "entities_in_scene",
        lambda hass, entity_id: [],
    )


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
        "automation_dependency_count": 0,
        "automation_dependencies": [],
        "script_dependency_count": 0,
        "script_dependencies": [],
        "scene_dependency_count": 0,
        "scene_dependencies": [],
        "unreferenced_entity_count": 0,
        "unreferenced_entities": [],
        "missing_entity_count": 0,
        "missing_entities": [],
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


@pytest.mark.asyncio
async def test_collect_automation_dependencies(monkeypatch) -> None:
    registry = SimpleNamespace(
        entities={
            "z": SimpleNamespace(
                entity_id="automation.z_rule",
                domain="automation",
                name=None,
                original_name="Z rule",
                disabled_by=None,
                entity_category=None,
                area_id=None,
                device_id=None,
            ),
            "a": SimpleNamespace(
                entity_id="automation.a_rule",
                domain="automation",
                name="A rule",
                original_name=None,
                disabled_by=None,
                entity_category=None,
                area_id=None,
                device_id=None,
            ),
            "sensor": SimpleNamespace(
                entity_id="sensor.temperature",
                domain="sensor",
                name="Temperature",
                original_name=None,
                disabled_by=None,
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

    referenced_entities = {
        "automation.a_rule": [
            "light.kitchen",
            "binary_sensor.motion",
            "light.kitchen",
        ],
        "automation.z_rule": [],
    }

    monkeypatch.setattr(
        entities_module,
        "entities_in_automation",
        lambda hass, entity_id: referenced_entities[entity_id],
    )

    context = InspectionContext()

    await EntitiesCollector().collect(
        FakeHass([]),
        context,
    )

    assert context.entities.automation_dependency_count == 2

    assert [
        dependency.entity_id
        for dependency in context.entities.automation_dependencies
    ] == [
        "automation.a_rule",
        "automation.z_rule",
    ]

    first = context.entities.automation_dependencies[0]

    assert first.name == "A rule"
    assert first.referenced_entities == [
        "binary_sensor.motion",
        "light.kitchen",
    ]
    assert first.referenced_entity_count == 2

    second = context.entities.automation_dependencies[1]

    assert second.name == "Z rule"
    assert second.referenced_entities == []
    assert second.referenced_entity_count == 0



@pytest.mark.asyncio
async def test_collect_script_dependencies(monkeypatch) -> None:
    registry = SimpleNamespace(
        entities={
            "z": SimpleNamespace(
                entity_id="script.z_rule",
                domain="script",
                name=None,
                original_name="Z rule",
                disabled_by=None,
                entity_category=None,
                area_id=None,
                device_id=None,
            ),
            "a": SimpleNamespace(
                entity_id="script.a_rule",
                domain="script",
                name="A rule",
                original_name=None,
                disabled_by=None,
                entity_category=None,
                area_id=None,
                device_id=None,
            ),
            "sensor": SimpleNamespace(
                entity_id="sensor.temperature",
                domain="sensor",
                name="Temperature",
                original_name=None,
                disabled_by=None,
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

    referenced_entities = {
        "script.a_rule": [
            "light.kitchen",
            "binary_sensor.motion",
            "light.kitchen",
        ],
        "script.z_rule": [],
    }

    monkeypatch.setattr(
        entities_module,
        "entities_in_script",
        lambda hass, entity_id: referenced_entities[entity_id],
    )

    context = InspectionContext()

    await EntitiesCollector().collect(
        FakeHass([]),
        context,
    )

    assert context.entities.script_dependency_count == 2

    assert [
        dependency.entity_id
        for dependency in context.entities.script_dependencies
    ] == [
        "script.a_rule",
        "script.z_rule",
    ]

    first = context.entities.script_dependencies[0]

    assert first.name == "A rule"
    assert first.referenced_entities == [
        "binary_sensor.motion",
        "light.kitchen",
    ]
    assert first.referenced_entity_count == 2

    second = context.entities.script_dependencies[1]

    assert second.name == "Z rule"
    assert second.referenced_entities == []
    assert second.referenced_entity_count == 0


@pytest.mark.asyncio
async def test_collect_scene_dependencies(monkeypatch) -> None:
    registry = SimpleNamespace(
        entities={
            "z": SimpleNamespace(
                entity_id="scene.z_scene",
                domain="scene",
                name=None,
                original_name="Z scene",
                disabled_by=None,
                entity_category=None,
                area_id=None,
                device_id=None,
            ),
            "a": SimpleNamespace(
                entity_id="scene.a_scene",
                domain="scene",
                name="A scene",
                original_name=None,
                disabled_by=None,
                entity_category=None,
                area_id=None,
                device_id=None,
            ),
            "sensor": SimpleNamespace(
                entity_id="sensor.temperature",
                domain="sensor",
                name="Temperature",
                original_name=None,
                disabled_by=None,
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

    referenced_entities = {
        "scene.a_scene": [
            "light.kitchen",
            "media_player.tv",
            "light.kitchen",
        ],
        "scene.z_scene": [],
    }

    monkeypatch.setattr(
        entities_module,
        "entities_in_scene",
        lambda hass, entity_id: referenced_entities[entity_id],
    )

    context = InspectionContext()

    await EntitiesCollector().collect(
        FakeHass([]),
        context,
    )

    assert context.entities.scene_dependency_count == 2

    assert [
        dependency.entity_id
        for dependency in context.entities.scene_dependencies
    ] == [
        "scene.a_scene",
        "scene.z_scene",
    ]

    first = context.entities.scene_dependencies[0]

    assert first.name == "A scene"
    assert first.referenced_entities == [
        "light.kitchen",
        "media_player.tv",
    ]
    assert first.referenced_entity_count == 2

    second = context.entities.scene_dependencies[1]

    assert second.name == "Z scene"
    assert second.referenced_entities == []
    assert second.referenced_entity_count == 0


@pytest.mark.asyncio
async def test_collect_unreferenced_entities(monkeypatch) -> None:
    registry = SimpleNamespace(
        entities={
            "automation": SimpleNamespace(
                entity_id="automation.kitchen",
                domain="automation",
                name="Kitchen automation",
                original_name=None,
                disabled_by=None,
                entity_category=None,
                area_id=None,
                device_id=None,
            ),
            "script": SimpleNamespace(
                entity_id="script.evening",
                domain="script",
                name="Evening",
                original_name=None,
                disabled_by=None,
                entity_category=None,
                area_id=None,
                device_id=None,
            ),
            "scene": SimpleNamespace(
                entity_id="scene.movie",
                domain="scene",
                name="Movie",
                original_name=None,
                disabled_by=None,
                entity_category=None,
                area_id=None,
                device_id=None,
            ),
            "automation_used": SimpleNamespace(
                entity_id="sensor.automation_used",
                domain="sensor",
                name="Automation used",
                original_name=None,
                disabled_by=None,
                entity_category=None,
                area_id=None,
                device_id=None,
            ),
            "script_used": SimpleNamespace(
                entity_id="light.script_used",
                domain="light",
                name="Script used",
                original_name=None,
                disabled_by=None,
                entity_category=None,
                area_id=None,
                device_id=None,
            ),
            "scene_used": SimpleNamespace(
                entity_id="switch.scene_used",
                domain="switch",
                name="Scene used",
                original_name=None,
                disabled_by=None,
                entity_category=None,
                area_id=None,
                device_id=None,
            ),
            "sensor_unreferenced": SimpleNamespace(
                entity_id="sensor.unreferenced",
                domain="sensor",
                name="Unreferenced",
                original_name=None,
                disabled_by=None,
                entity_category=None,
                area_id=None,
                device_id=None,
            ),
            "binary_unreferenced": SimpleNamespace(
                entity_id="binary_sensor.unreferenced",
                domain="binary_sensor",
                name="Unreferenced binary",
                original_name=None,
                disabled_by=None,
                entity_category=None,
                area_id=None,
                device_id=None,
            ),
            "disabled": SimpleNamespace(
                entity_id="sensor.disabled_candidate",
                domain="sensor",
                name="Disabled candidate",
                original_name=None,
                disabled_by="user",
                entity_category=None,
                area_id=None,
                device_id=None,
            ),
            "diagnostic": SimpleNamespace(
                entity_id="sensor.diagnostic_candidate",
                domain="sensor",
                name="Diagnostic candidate",
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
        lambda hass: FakeDeviceRegistry(),
    )

    monkeypatch.setattr(
        entities_module,
        "entities_in_automation",
        lambda hass, entity_id: ["sensor.automation_used"],
    )
    monkeypatch.setattr(
        entities_module,
        "entities_in_script",
        lambda hass, entity_id: ["light.script_used"],
    )
    monkeypatch.setattr(
        entities_module,
        "entities_in_scene",
        lambda hass, entity_id: ["switch.scene_used"],
    )

    states = [
        FakeState(
            "automation.kitchen",
            "on",
            "Kitchen automation",
        ),
        FakeState(
            "script.evening",
            "off",
            "Evening",
        ),
        FakeState(
            "scene.movie",
            "scening",
            "Movie",
        ),
        FakeState(
            "sensor.automation_used",
            "20",
            "Automation used",
        ),
        FakeState(
            "light.script_used",
            "on",
            "Script used",
        ),
        FakeState(
            "switch.scene_used",
            "off",
            "Scene used",
        ),
        FakeState(
            "sensor.unreferenced",
            "10",
            "Unreferenced",
        ),
        FakeState(
            "binary_sensor.unreferenced",
            "off",
            "Unreferenced binary",
        ),
        FakeState(
            "sensor.disabled_candidate",
            "10",
            "Disabled candidate",
        ),
        FakeState(
            "sensor.diagnostic_candidate",
            "10",
            "Diagnostic candidate",
        ),
        FakeState(
            "sensor.runtime_only",
            "10",
            "Runtime only",
        ),
    ]

    context = InspectionContext()

    await EntitiesCollector().collect(
        FakeHass(states),
        context,
    )

    assert context.entities.unreferenced_entity_count == 2
    assert [
        entity.entity_id
        for entity in context.entities.unreferenced_entities
    ] == [
        "binary_sensor.unreferenced",
        "sensor.unreferenced",
    ]

    assert context.entities.unreferenced_entities[0].name == (
        "Unreferenced binary"
    )
    assert context.entities.unreferenced_entities[0].domain == (
        "binary_sensor"
    )


@pytest.mark.asyncio
async def test_collect_missing_entity_references(monkeypatch) -> None:
    registry = SimpleNamespace(
        entities={
            "automation": SimpleNamespace(
                entity_id="automation.kitchen",
                domain="automation",
                name="Kitchen",
                original_name=None,
                disabled_by=None,
                entity_category=None,
                area_id=None,
                device_id=None,
            ),
            "script": SimpleNamespace(
                entity_id="script.evening",
                domain="script",
                name="Evening",
                original_name=None,
                disabled_by=None,
                entity_category=None,
                area_id=None,
                device_id=None,
            ),
            "scene": SimpleNamespace(
                entity_id="scene.movie",
                domain="scene",
                name="Movie",
                original_name=None,
                disabled_by=None,
                entity_category=None,
                area_id=None,
                device_id=None,
            ),
            "registered": SimpleNamespace(
                entity_id="sensor.registered",
                domain="sensor",
                name="Registered",
                original_name=None,
                disabled_by=None,
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

    monkeypatch.setattr(
        entities_module,
        "entities_in_automation",
        lambda hass, entity_id: [
            "sensor.registered",
            "switch.automation_missing",
            "switch.shared_missing",
        ],
    )
    monkeypatch.setattr(
        entities_module,
        "entities_in_script",
        lambda hass, entity_id: [
            "sensor.runtime_only",
            "light.script_missing",
            "switch.shared_missing",
        ],
    )
    monkeypatch.setattr(
        entities_module,
        "entities_in_scene",
        lambda hass, entity_id: [
            "binary_sensor.scene_missing",
        ],
    )

    states = [
        FakeState(
            "automation.kitchen",
            "on",
            "Kitchen",
        ),
        FakeState(
            "script.evening",
            "off",
            "Evening",
        ),
        FakeState(
            "scene.movie",
            "scening",
            "Movie",
        ),
        FakeState(
            "sensor.registered",
            "20",
            "Registered",
        ),
        FakeState(
            "sensor.runtime_only",
            "10",
            "Runtime only",
        ),
    ]

    context = InspectionContext()

    await EntitiesCollector().collect(
        FakeHass(states),
        context,
    )

    assert context.entities.missing_entity_count == 4
    assert context.entities.missing_entities == [
        "binary_sensor.scene_missing",
        "light.script_missing",
        "switch.automation_missing",
        "switch.shared_missing",
    ]
