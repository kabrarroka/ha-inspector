"""Tests for the public remediation progress query service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
import voluptuous as vol

from custom_components.ha_inspector import (
    SERVICE_REMEDIATION_PROGRESS,
    SERVICE_REMEDIATION_PROGRESS_SCHEMA,
    async_setup,
)
from custom_components.ha_inspector.const import (
    DATA_LAST_RESULT,
    DOMAIN,
)
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
async def test_remediation_progress_service_is_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Remediation progress query service is registered."""
    _, registrations = await _setup_services(monkeypatch)

    assert SERVICE_REMEDIATION_PROGRESS in registrations


def test_remediation_progress_schema_accepts_no_fields() -> None:
    """Remediation progress query accepts no request fields."""
    assert SERVICE_REMEDIATION_PROGRESS_SCHEMA({}) == {}

    with pytest.raises(vol.MultipleInvalid):
        SERVICE_REMEDIATION_PROGRESS_SCHEMA({"unexpected": True})


def test_remediation_progress_is_part_of_public_api() -> None:
    """Remediation progress query is advertised by the public API."""
    assert "remediation_progress" in PUBLIC_SERVICES


@pytest.mark.asyncio
async def test_remediation_progress_returns_latest_inspection_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Latest remediation progress and lifecycle state are returned."""
    hass, registrations = await _setup_services(monkeypatch)

    progress = {
        "tracked_entities": 2,
        "pending": 1,
        "in_progress": 1,
        "resolved": 0,
        "total_actions": 3,
        "completed_actions": 1,
        "remaining_actions": 2,
        "new_references": 0,
        "entities": [
            {
                "entity_id": "sensor.first",
                "status": "in_progress",
                "total_action_count": 2,
                "completed_action_count": 1,
                "remaining_action_count": 1,
                "new_reference_count": 0,
            },
            {
                "entity_id": "sensor.second",
                "status": "pending",
                "total_action_count": 1,
                "completed_action_count": 0,
                "remaining_action_count": 1,
                "new_reference_count": 0,
            },
        ],
    }
    lifecycle = {
        "status": "progressing",
        "tracked_entities": 2,
        "pending": 1,
        "in_progress": 1,
        "resolved": 0,
        "completed_actions": 1,
        "remaining_actions": 2,
        "new_references": 0,
        "resolved_since_previous": 0,
        "newly_pending_since_previous": 0,
        "new_references_delta": 0,
    }

    hass.data[DOMAIN] = {
        DATA_LAST_RESULT: {
            "remediation_progress": progress,
            "remediation_lifecycle": lifecycle,
        }
    }

    response = await registrations[SERVICE_REMEDIATION_PROGRESS](MagicMock())

    assert response == {
        "progress": progress,
        "lifecycle": lifecycle,
    }


@pytest.mark.asyncio
async def test_remediation_progress_returns_empty_state_without_inspection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing inspection data returns canonical empty lifecycle state."""
    _, registrations = await _setup_services(monkeypatch)

    response = await registrations[SERVICE_REMEDIATION_PROGRESS](MagicMock())

    assert response == {
        "progress": {
            "tracked_entities": 0,
            "pending": 0,
            "in_progress": 0,
            "resolved": 0,
            "total_actions": 0,
            "completed_actions": 0,
            "remaining_actions": 0,
            "new_references": 0,
            "entities": [],
        },
        "lifecycle": {
            "status": "idle",
            "tracked_entities": 0,
            "pending": 0,
            "in_progress": 0,
            "resolved": 0,
            "completed_actions": 0,
            "remaining_actions": 0,
            "new_references": 0,
            "resolved_since_previous": 0,
            "newly_pending_since_previous": 0,
            "new_references_delta": 0,
        },
    }


@pytest.mark.asyncio
async def test_remediation_progress_normalizes_malformed_latest_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Malformed stored remediation data falls back to empty state."""
    hass, registrations = await _setup_services(monkeypatch)

    hass.data[DOMAIN] = {
        DATA_LAST_RESULT: {
            "remediation_progress": "invalid",
            "remediation_lifecycle": ["invalid"],
        }
    }

    response = await registrations[SERVICE_REMEDIATION_PROGRESS](
        MagicMock()
    )

    assert response == {
        "progress": {
            "tracked_entities": 0,
            "pending": 0,
            "in_progress": 0,
            "resolved": 0,
            "total_actions": 0,
            "completed_actions": 0,
            "remaining_actions": 0,
            "new_references": 0,
            "entities": [],
        },
        "lifecycle": {
            "status": "idle",
            "tracked_entities": 0,
            "pending": 0,
            "in_progress": 0,
            "resolved": 0,
            "completed_actions": 0,
            "remaining_actions": 0,
            "new_references": 0,
            "resolved_since_previous": 0,
            "newly_pending_since_previous": 0,
            "new_references_delta": 0,
        },
    }
