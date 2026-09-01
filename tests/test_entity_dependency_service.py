"""Tests for the public entity dependency query service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
import voluptuous as vol

from custom_components.ha_inspector import (
    SERVICE_ENTITY_DEPENDENCY,
    SERVICE_ENTITY_DEPENDENCY_SCHEMA,
    async_setup,
)
from custom_components.ha_inspector.const import DOMAIN


async def _setup_services(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[MagicMock, dict[str, object]]:
    """Set up HA Inspector services for tests."""
    inspector_type = MagicMock()
    registry = MagicMock()

    monkeypatch.setattr(
        "custom_components.ha_inspector._load_engine",
        lambda: (inspector_type, registry),
    )

    hass = MagicMock()
    hass.data = {}
    hass.async_add_executor_job = AsyncMock(
        return_value=(inspector_type, registry)
    )

    await async_setup(hass, {})

    registrations = {
        call.args[1]: call.args[2]
        for call in hass.services.async_register.call_args_list
        if call.args[0] == DOMAIN
    }

    return hass, registrations


@pytest.mark.asyncio
async def test_entity_dependency_service_is_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Entity dependency query service is registered."""
    _, registrations = await _setup_services(monkeypatch)

    assert SERVICE_ENTITY_DEPENDENCY in registrations


def test_entity_dependency_schema_requires_entity_id() -> None:
    """Entity dependency query requires exactly one entity ID."""
    assert SERVICE_ENTITY_DEPENDENCY_SCHEMA(
        {"entity_id": "sensor.temperature"}
    ) == {
        "entity_id": "sensor.temperature"
    }

    with pytest.raises(vol.MultipleInvalid):
        SERVICE_ENTITY_DEPENDENCY_SCHEMA({})

    with pytest.raises(vol.MultipleInvalid):
        SERVICE_ENTITY_DEPENDENCY_SCHEMA(
            {
                "entity_id": "sensor.temperature",
                "unexpected": True,
            }
        )


@pytest.mark.asyncio
async def test_entity_dependency_returns_live_reference_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Service returns active and disabled references for one entity."""
    from types import SimpleNamespace

    _, registrations = await _setup_services(monkeypatch)

    entries = {
        "target": SimpleNamespace(
            entity_id="sensor.temperature",
            domain="sensor",
            disabled_by=None,
            name="Temperature",
            original_name=None,
        ),
        "automation_active": SimpleNamespace(
            entity_id="automation.active",
            domain="automation",
            disabled_by=None,
            name="Active automation",
            original_name=None,
        ),
        "automation_disabled": SimpleNamespace(
            entity_id="automation.disabled",
            domain="automation",
            disabled_by="user",
            name="Disabled automation",
            original_name=None,
        ),
        "script_active": SimpleNamespace(
            entity_id="script.active",
            domain="script",
            disabled_by=None,
            name="Active script",
            original_name=None,
        ),
        "scene_disabled": SimpleNamespace(
            entity_id="scene.disabled",
            domain="scene",
            disabled_by="integration",
            name="Disabled scene",
            original_name=None,
        ),
    }

    registry = SimpleNamespace(entities=entries)

    monkeypatch.setattr(
        "homeassistant.helpers.entity_registry.async_get",
        lambda _hass: registry,
    )
    monkeypatch.setattr(
        "homeassistant.components.automation.entities_in_automation",
        lambda _hass, entity_id: (
            ["sensor.temperature"]
            if entity_id in {
                "automation.active",
                "automation.disabled",
            }
            else []
        ),
    )
    monkeypatch.setattr(
        "homeassistant.components.script.entities_in_script",
        lambda _hass, entity_id: (
            ["sensor.temperature"]
            if entity_id == "script.active"
            else []
        ),
    )
    monkeypatch.setattr(
        "homeassistant.components.homeassistant.scene.entities_in_scene",
        lambda _hass, entity_id: (
            ["sensor.temperature"]
            if entity_id == "scene.disabled"
            else []
        ),
    )

    call = MagicMock()
    call.data = {"entity_id": "sensor.temperature"}

    response = await registrations[SERVICE_ENTITY_DEPENDENCY](call)

    assert response == {
        "entity_id": "sensor.temperature",
        "exists": True,
        "referenced": True,
        "reference_count": 4,
        "active_reference_count": 2,
        "disabled_reference_count": 2,
        "automation_reference_count": 2,
        "script_reference_count": 1,
        "scene_reference_count": 1,
        "active_automation_references": ["automation.active"],
        "disabled_automation_references": ["automation.disabled"],
        "active_script_references": ["script.active"],
        "disabled_script_references": [],
        "active_scene_references": [],
        "disabled_scene_references": ["scene.disabled"],
    }


@pytest.mark.asyncio
async def test_entity_dependency_returns_zero_impact_for_existing_unreferenced_entity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Existing entities without references return an empty impact summary."""
    from types import SimpleNamespace

    _, registrations = await _setup_services(monkeypatch)

    entries = {
        "target": SimpleNamespace(
            entity_id="sensor.unused",
            domain="sensor",
            disabled_by=None,
            name="Unused",
            original_name=None,
        ),
    }

    registry = SimpleNamespace(entities=entries)

    monkeypatch.setattr(
        "homeassistant.helpers.entity_registry.async_get",
        lambda _hass: registry,
    )

    call = MagicMock()
    call.data = {"entity_id": "sensor.unused"}

    response = await registrations[SERVICE_ENTITY_DEPENDENCY](call)

    assert response == {
        "entity_id": "sensor.unused",
        "exists": True,
        "referenced": False,
        "reference_count": 0,
        "active_reference_count": 0,
        "disabled_reference_count": 0,
        "automation_reference_count": 0,
        "script_reference_count": 0,
        "scene_reference_count": 0,
        "active_automation_references": [],
        "disabled_automation_references": [],
        "active_script_references": [],
        "disabled_script_references": [],
        "active_scene_references": [],
        "disabled_scene_references": [],
    }


@pytest.mark.asyncio
async def test_entity_dependency_marks_missing_referenced_entity_as_nonexistent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing entities can still expose stale configuration references."""
    from types import SimpleNamespace

    hass, registrations = await _setup_services(monkeypatch)

    entries = {
        "automation_active": SimpleNamespace(
            entity_id="automation.active",
            domain="automation",
            disabled_by=None,
            name="Active automation",
            original_name=None,
        ),
    }

    registry = SimpleNamespace(entities=entries)

    monkeypatch.setattr(
        "homeassistant.helpers.entity_registry.async_get",
        lambda _hass: registry,
    )
    monkeypatch.setattr(
        "homeassistant.components.automation.entities_in_automation",
        lambda _hass, entity_id: (
            ["sensor.missing"]
            if entity_id == "automation.active"
            else []
        ),
    )

    hass.states.get.return_value = None

    call = MagicMock()
    call.data = {"entity_id": "sensor.missing"}

    response = await registrations[SERVICE_ENTITY_DEPENDENCY](call)

    assert response == {
        "entity_id": "sensor.missing",
        "exists": False,
        "referenced": True,
        "reference_count": 1,
        "active_reference_count": 1,
        "disabled_reference_count": 0,
        "automation_reference_count": 1,
        "script_reference_count": 0,
        "scene_reference_count": 0,
        "active_automation_references": ["automation.active"],
        "disabled_automation_references": [],
        "active_script_references": [],
        "disabled_script_references": [],
        "active_scene_references": [],
        "disabled_scene_references": [],
    }


@pytest.mark.asyncio
async def test_entity_dependency_ignores_internal_entity_registry_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Internal entity registry IDs are not exposed as dependencies."""
    from types import SimpleNamespace

    hass, registrations = await _setup_services(monkeypatch)

    internal_entity_registry_id = "0123456789abcdef0123456789abcdef"

    entries = {
        "automation_active": SimpleNamespace(
            entity_id="automation.active",
            domain="automation",
            disabled_by=None,
            name="Active automation",
            original_name=None,
        ),
    }

    registry = SimpleNamespace(entities=entries)

    monkeypatch.setattr(
        "homeassistant.helpers.entity_registry.async_get",
        lambda _hass: registry,
    )
    monkeypatch.setattr(
        "homeassistant.components.automation.entities_in_automation",
        lambda _hass, entity_id: (
            [internal_entity_registry_id]
            if entity_id == "automation.active"
            else []
        ),
    )

    hass.states.get.return_value = None

    call = MagicMock()
    call.data = {"entity_id": internal_entity_registry_id}

    response = await registrations[SERVICE_ENTITY_DEPENDENCY](call)

    assert response["exists"] is False
    assert response["referenced"] is False
    assert response["reference_count"] == 0
    assert response["active_automation_references"] == []
