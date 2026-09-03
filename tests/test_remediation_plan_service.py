"""Tests for the public remediation plan query service."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import voluptuous as vol

from custom_components.ha_inspector import (
    SERVICE_REMEDIATION_PLAN,
    SERVICE_REMEDIATION_PLAN_SCHEMA,
    async_setup,
)
from custom_components.ha_inspector.const import DOMAIN
from custom_components.ha_inspector.engine.public_api import PUBLIC_SERVICES


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
async def test_remediation_plan_service_is_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Remediation plan query service is registered."""
    _, registrations = await _setup_services(monkeypatch)

    assert SERVICE_REMEDIATION_PLAN in registrations


def test_remediation_plan_schema_requires_entity_id() -> None:
    """Remediation plan query requires exactly one entity ID."""
    assert SERVICE_REMEDIATION_PLAN_SCHEMA(
        {"entity_id": "sensor.temperature"}
    ) == {
        "entity_id": "sensor.temperature"
    }

    with pytest.raises(vol.MultipleInvalid):
        SERVICE_REMEDIATION_PLAN_SCHEMA({})

    with pytest.raises(vol.MultipleInvalid):
        SERVICE_REMEDIATION_PLAN_SCHEMA(
            {
                "entity_id": "sensor.temperature",
                "unexpected": True,
            }
        )


def test_remediation_plan_is_part_of_public_api() -> None:
    """Remediation plan query is advertised by the public API."""
    assert "remediation_plan" in PUBLIC_SERVICES


@pytest.mark.asyncio
async def test_remediation_plan_returns_live_plan_for_missing_referenced_entity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing referenced entities expose a live remediation plan."""
    from types import SimpleNamespace

    hass, registrations = await _setup_services(monkeypatch)
    hass.states.get.return_value = None

    entries = {
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
            if entity_id in {
                "automation.active",
                "automation.disabled",
            }
            else []
        ),
    )

    call = MagicMock()
    call.data = {"entity_id": "sensor.missing"}

    response = await registrations[SERVICE_REMEDIATION_PLAN](call)

    assert response == {
        "entity_id": "sensor.missing",
        "plan": {
            "action": "review_active_references",
            "safety": "review_required",
            "reason": "Entity is referenced by active configuration",
            "reference_count": 2,
            "active_reference_count": 1,
            "disabled_reference_count": 1,
            "steps": [
                {
                    "configuration_type": "automation",
                    "configuration_id": "automation.active",
                    "status": "active",
                    "action": "review_entity_reference",
                },
                {
                    "configuration_type": "automation",
                    "configuration_id": "automation.disabled",
                    "status": "disabled",
                    "action": "review_entity_reference",
                },
            ],
        },
        "classification": {
            "safety": "review_required",
            "confidence": "high",
            "reason": "Entity is referenced by active configuration",
        },
        "impact_preview": {
            "current_reference_count": 2,
            "affected_configuration_count": 2,
            "removable_reference_count": 0,
            "review_reference_count": 2,
            "projected_reference_count": 2,
        },
    }


@pytest.mark.asyncio
async def test_remediation_plan_returns_likely_safe_disabled_only_plan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Disabled-only references expose a removable likely-safe plan."""
    from types import SimpleNamespace

    hass, registrations = await _setup_services(monkeypatch)
    hass.states.get.return_value = None

    entries = {
        "automation_disabled": SimpleNamespace(
            entity_id="automation.disabled",
            domain="automation",
            disabled_by="user",
            name="Disabled automation",
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
            if entity_id == "automation.disabled"
            else []
        ),
    )

    call = MagicMock()
    call.data = {"entity_id": "sensor.missing"}

    response = await registrations[SERVICE_REMEDIATION_PLAN](call)

    assert response == {
        "entity_id": "sensor.missing",
        "plan": {
            "action": "remove_disabled_references",
            "safety": "likely_safe",
            "reason": "Entity is referenced only by disabled configuration",
            "reference_count": 1,
            "active_reference_count": 0,
            "disabled_reference_count": 1,
            "steps": [
                {
                    "configuration_type": "automation",
                    "configuration_id": "automation.disabled",
                    "status": "disabled",
                    "action": "remove_entity_reference",
                },
            ],
        },
        "classification": {
            "safety": "likely_safe",
            "confidence": "high",
            "reason": "Entity is referenced only by disabled configuration",
        },
        "impact_preview": {
            "current_reference_count": 1,
            "affected_configuration_count": 1,
            "removable_reference_count": 1,
            "review_reference_count": 0,
            "projected_reference_count": 0,
        },
    }


@pytest.mark.asyncio
async def test_remediation_plan_returns_none_when_no_references_exist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Entities without dependency references do not require remediation."""
    from types import SimpleNamespace

    _, registrations = await _setup_services(monkeypatch)

    registry = SimpleNamespace(entities={})

    monkeypatch.setattr(
        "homeassistant.helpers.entity_registry.async_get",
        lambda _hass: registry,
    )

    call = MagicMock()
    call.data = {"entity_id": "sensor.unused"}

    response = await registrations[SERVICE_REMEDIATION_PLAN](call)

    assert response == {
        "entity_id": "sensor.unused",
        "plan": None,
        "classification": None,
        "impact_preview": None,
    }


@pytest.mark.asyncio
async def test_remediation_plan_ignores_existing_referenced_entity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Existing referenced entities do not require stale-reference remediation."""
    hass, registrations = await _setup_services(monkeypatch)

    registry = MagicMock()
    registry.entities.values.return_value = [
        SimpleNamespace(
            entity_id="sensor.existing",
            domain="sensor",
            name="Existing",
            original_name=None,
            disabled_by=None,
        ),
        SimpleNamespace(
            entity_id="automation.active",
            domain="automation",
            name="Active",
            original_name=None,
            disabled_by=None,
        ),
    ]

    monkeypatch.setattr(
        "custom_components.ha_inspector.engine.live_dependency_context.er.async_get",
        lambda _hass: registry,
    )
    monkeypatch.setattr(
        "homeassistant.components.automation.entities_in_automation",
        lambda _hass, entity_id: (
            {"sensor.existing"}
            if entity_id == "automation.active"
            else set()
        ),
    )

    hass.states.get.return_value = None

    call = MagicMock()
    call.data = {"entity_id": "sensor.existing"}

    response = await registrations["remediation_plan"](call)

    assert response == {
        "entity_id": "sensor.existing",
        "plan": None,
        "classification": None,
        "impact_preview": None,
    }
