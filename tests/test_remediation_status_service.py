"""Tests for the public remediation status query service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
import voluptuous as vol

from custom_components.ha_inspector import async_setup
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
async def test_remediation_status_service_is_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Remediation status query service is registered."""
    _, registrations = await _setup_services(monkeypatch)

    assert "remediation_status" in registrations


def test_remediation_status_schema_accepts_optional_entity_id() -> None:
    """Remediation status accepts an optional entity ID."""
    from custom_components.ha_inspector import (
        SERVICE_REMEDIATION_STATUS_SCHEMA,
    )

    assert SERVICE_REMEDIATION_STATUS_SCHEMA({}) == {}

    assert SERVICE_REMEDIATION_STATUS_SCHEMA(
        {"entity_id": "sensor.temperature"}
    ) == {
        "entity_id": "sensor.temperature"
    }

    with pytest.raises(vol.MultipleInvalid):
        SERVICE_REMEDIATION_STATUS_SCHEMA(
            {"unexpected": True}
        )


def test_remediation_status_is_part_of_public_api() -> None:
    """Remediation status query is advertised by the public API."""
    assert "remediation_status" in PUBLIC_SERVICES


@pytest.mark.asyncio
async def test_remediation_status_returns_latest_inspection_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """General status query returns the latest remediation diagnostics."""
    from copy import deepcopy

    from custom_components.ha_inspector.const import DATA_LAST_RESULT

    hass, registrations = await _setup_services(monkeypatch)

    dashboard = {
        "status": "active",
        "tracked_entities": 2,
        "pending": 1,
        "in_progress": 1,
        "resolved": 0,
        "completed_actions": 1,
        "remaining_actions": 2,
        "new_references": 0,
        "stalled_entities": 0,
        "high_urgency_entities": 1,
        "oldest_active_age_seconds": 86400.0,
        "trend": "improving",
        "regression_count": 0,
        "remaining_actions_regression_count": 0,
        "new_references_regression_count": 0,
    }

    entities = [
        {
            "entity_id": "sensor.first",
            "status": "in_progress",
            "age_seconds": 86400.0,
            "stalled": False,
            "urgency": "high",
            "total_action_count": 2,
            "completed_action_count": 1,
            "remaining_action_count": 1,
            "new_reference_count": 0,
        },
        {
            "entity_id": "sensor.second",
            "status": "pending",
            "age_seconds": 3600.0,
            "stalled": False,
            "urgency": "low",
            "total_action_count": 1,
            "completed_action_count": 0,
            "remaining_action_count": 1,
            "new_reference_count": 0,
        },
    ]

    latest_result = {
        "remediation_dashboard_summary": dashboard,
        "remediation_entity_summaries": entities,
    }

    original_result = deepcopy(latest_result)

    hass.data.setdefault(DOMAIN, {})[DATA_LAST_RESULT] = latest_result

    call = MagicMock()
    call.data = {}

    response = await registrations["remediation_status"](call)

    assert response == {
        "status": "available",
        "source": "latest_inspection",
        "dashboard": dashboard,
        "entities": entities,
    }

    assert latest_result == original_result

    assert response["dashboard"] is not dashboard
    assert response["entities"] is not entities


@pytest.mark.asyncio
async def test_remediation_status_returns_requested_entity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Entity query returns only the requested remediation summary."""
    from copy import deepcopy

    from custom_components.ha_inspector.const import DATA_LAST_RESULT

    hass, registrations = await _setup_services(monkeypatch)

    entity = {
        "entity_id": "sensor.temperature",
        "status": "in_progress",
        "age_seconds": 3600.0,
        "stalled": False,
        "urgency": "medium",
        "total_action_count": 2,
        "completed_action_count": 1,
        "remaining_action_count": 1,
        "new_reference_count": 0,
    }

    other_entity = {
        **entity,
        "entity_id": "sensor.humidity",
        "status": "pending",
    }

    entities = [other_entity, entity]
    original_entities = deepcopy(entities)

    hass.data.setdefault(DOMAIN, {})[DATA_LAST_RESULT] = {
        "remediation_dashboard_summary": {
            "status": "active",
        },
        "remediation_entity_summaries": entities,
    }

    call = MagicMock()
    call.data = {"entity_id": "sensor.temperature"}

    response = await registrations["remediation_status"](call)

    assert response == {
        "status": "available",
        "source": "latest_inspection",
        "entity": entity,
    }

    assert entities == original_entities
    assert response["entity"] is not entity


@pytest.mark.asyncio
async def test_remediation_status_returns_not_found_for_unknown_entity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unknown entity returns an explicit not-found status."""
    from custom_components.ha_inspector.const import DATA_LAST_RESULT

    hass, registrations = await _setup_services(monkeypatch)

    hass.data.setdefault(DOMAIN, {})[DATA_LAST_RESULT] = {
        "remediation_dashboard_summary": {
            "status": "active",
        },
        "remediation_entity_summaries": [
            {
                "entity_id": "sensor.temperature",
                "status": "pending",
            },
        ],
    }

    call = MagicMock()
    call.data = {"entity_id": "sensor.unknown"}

    response = await registrations["remediation_status"](call)

    assert response == {
        "status": "not_found",
        "source": "latest_inspection",
        "entity": None,
    }


@pytest.mark.asyncio
async def test_remediation_status_returns_persisted_general_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """General query falls back to persisted remediation state."""
    from custom_components.ha_inspector.const import DATA_REMEDIATION_STATE

    hass, registrations = await _setup_services(monkeypatch)

    progress = {
        "tracked_entities": 1,
        "pending": 1,
        "in_progress": 0,
        "resolved": 0,
        "total_actions": 2,
        "completed_actions": 0,
        "remaining_actions": 2,
        "new_references": 0,
        "entities": [
            {
                "entity_id": "sensor.temperature",
                "status": "pending",
                "total_action_count": 2,
                "completed_action_count": 0,
                "remaining_action_count": 2,
                "new_reference_count": 0,
            },
        ],
    }

    lifecycle = {
        "status": "active",
        "tracked_entities": 1,
        "pending": 1,
        "in_progress": 0,
        "resolved": 0,
        "completed_actions": 0,
        "remaining_actions": 2,
        "new_references": 0,
        "resolved_since_previous": 0,
        "newly_pending_since_previous": 0,
        "new_references_delta": 0,
    }

    remediation_state = MagicMock()
    remediation_state.state.return_value = {
        "progress": progress,
        "lifecycle": lifecycle,
    }

    hass.data.setdefault(DOMAIN, {})[
        DATA_REMEDIATION_STATE
    ] = remediation_state

    call = MagicMock()
    call.data = {}

    response = await registrations["remediation_status"](call)

    assert response == {
        "status": "available",
        "source": "persisted_state",
        "dashboard": None,
        "entities": [],
        "progress": progress,
        "lifecycle": lifecycle,
    }

    assert response["progress"] is not progress
    assert response["lifecycle"] is not lifecycle


@pytest.mark.asyncio
async def test_remediation_status_returns_persisted_entity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Entity query uses basic persisted progress after restart."""
    from custom_components.ha_inspector.const import DATA_REMEDIATION_STATE

    hass, registrations = await _setup_services(monkeypatch)

    entity = {
        "entity_id": "sensor.temperature",
        "status": "pending",
        "total_action_count": 2,
        "completed_action_count": 0,
        "remaining_action_count": 2,
        "new_reference_count": 0,
    }

    progress = {
        "tracked_entities": 1,
        "entities": [entity],
    }

    lifecycle = {
        "status": "active",
        "tracked_entities": 1,
    }

    remediation_state = MagicMock()
    remediation_state.state.return_value = {
        "progress": progress,
        "lifecycle": lifecycle,
    }

    hass.data.setdefault(DOMAIN, {})[
        DATA_REMEDIATION_STATE
    ] = remediation_state

    call = MagicMock()
    call.data = {"entity_id": "sensor.temperature"}

    response = await registrations["remediation_status"](call)

    assert response == {
        "status": "available",
        "source": "persisted_state",
        "entity": entity,
    }

    assert response["entity"] is not entity


@pytest.mark.asyncio
async def test_remediation_status_without_available_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """General query reports unavailable when no diagnostics exist."""
    _, registrations = await _setup_services(monkeypatch)

    call = MagicMock()
    call.data = {}

    response = await registrations["remediation_status"](call)

    assert response == {
        "status": "unavailable",
        "source": "none",
        "dashboard": None,
        "entities": [],
    }


@pytest.mark.asyncio
async def test_remediation_status_entity_without_available_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Entity query reports unavailable without diagnostic information."""
    _, registrations = await _setup_services(monkeypatch)

    call = MagicMock()
    call.data = {"entity_id": "sensor.temperature"}

    response = await registrations["remediation_status"](call)

    assert response == {
        "status": "unavailable",
        "source": "none",
        "entity": None,
    }


@pytest.mark.asyncio
async def test_remediation_status_persisted_unknown_entity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unknown entity is not found when persisted entity data is available."""
    from custom_components.ha_inspector.const import DATA_REMEDIATION_STATE

    hass, registrations = await _setup_services(monkeypatch)

    remediation_state = MagicMock()
    remediation_state.state.return_value = {
        "progress": {
            "tracked_entities": 1,
            "entities": [
                {
                    "entity_id": "sensor.temperature",
                    "status": "pending",
                },
            ],
        },
        "lifecycle": {
            "status": "active",
        },
    }

    hass.data.setdefault(DOMAIN, {})[
        DATA_REMEDIATION_STATE
    ] = remediation_state

    call = MagicMock()
    call.data = {"entity_id": "sensor.unknown"}

    response = await registrations["remediation_status"](call)

    assert response == {
        "status": "not_found",
        "source": "persisted_state",
        "entity": None,
    }


@pytest.mark.asyncio
async def test_remediation_status_persisted_entity_without_entity_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing persisted entity collection cannot establish absence."""
    from custom_components.ha_inspector.const import DATA_REMEDIATION_STATE

    hass, registrations = await _setup_services(monkeypatch)

    remediation_state = MagicMock()
    remediation_state.state.return_value = {
        "progress": {
            "tracked_entities": 1,
            "pending": 1,
        },
        "lifecycle": {
            "status": "active",
        },
    }

    hass.data.setdefault(DOMAIN, {})[
        DATA_REMEDIATION_STATE
    ] = remediation_state

    call = MagicMock()
    call.data = {"entity_id": "sensor.temperature"}

    response = await registrations["remediation_status"](call)

    assert response == {
        "status": "unavailable",
        "source": "persisted_state",
        "entity": None,
    }


@pytest.mark.asyncio
async def test_remediation_status_rejects_incomplete_latest_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Incomplete latest diagnostics are not reported as available."""
    from custom_components.ha_inspector.const import DATA_LAST_RESULT

    hass, registrations = await _setup_services(monkeypatch)

    hass.data.setdefault(DOMAIN, {})[DATA_LAST_RESULT] = {
        "remediation_entity_summaries": [
            {
                "entity_id": "sensor.temperature",
                "status": "pending",
            },
        ],
    }

    call = MagicMock()
    call.data = {}

    response = await registrations["remediation_status"](call)

    assert response == {
        "status": "unavailable",
        "source": "none",
        "dashboard": None,
        "entities": [],
    }


@pytest.mark.asyncio
async def test_remediation_status_rejects_invalid_persisted_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invalid persisted progress or lifecycle is not exposed."""
    from custom_components.ha_inspector.const import DATA_REMEDIATION_STATE

    hass, registrations = await _setup_services(monkeypatch)

    remediation_state = MagicMock()
    remediation_state.state.return_value = {
        "progress": ["invalid"],
        "lifecycle": {
            "status": "active",
        },
    }

    hass.data.setdefault(DOMAIN, {})[
        DATA_REMEDIATION_STATE
    ] = remediation_state

    call = MagicMock()
    call.data = {}

    response = await registrations["remediation_status"](call)

    assert response == {
        "status": "unavailable",
        "source": "none",
        "dashboard": None,
        "entities": [],
    }


@pytest.mark.asyncio
async def test_remediation_status_prefers_latest_inspection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Latest inspection takes precedence over persisted state."""
    from custom_components.ha_inspector.const import (
        DATA_LAST_RESULT,
        DATA_REMEDIATION_STATE,
    )

    hass, registrations = await _setup_services(monkeypatch)

    dashboard = {
        "status": "active",
        "tracked_entities": 1,
    }

    entities = [
        {
            "entity_id": "sensor.temperature",
            "status": "in_progress",
        },
    ]

    remediation_state = MagicMock()

    hass.data.setdefault(DOMAIN, {}).update(
        {
            DATA_LAST_RESULT: {
                "remediation_dashboard_summary": dashboard,
                "remediation_entity_summaries": entities,
            },
            DATA_REMEDIATION_STATE: remediation_state,
        }
    )

    call = MagicMock()
    call.data = {}

    response = await registrations["remediation_status"](call)

    assert response == {
        "status": "available",
        "source": "latest_inspection",
        "dashboard": dashboard,
        "entities": entities,
    }

    remediation_state.state.assert_not_called()
