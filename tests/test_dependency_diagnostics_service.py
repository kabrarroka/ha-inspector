"""Tests for the dependency diagnostics service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
import voluptuous as vol

from custom_components.ha_inspector import (
    SERVICE_DEPENDENCY_DIAGNOSTICS_SCHEMA,
    async_setup,
)
from custom_components.ha_inspector.const import DATA_LAST_RESULT, DOMAIN


async def _setup_services(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[MagicMock, dict[str, object]]:
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
async def test_dependency_diagnostics_service_is_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dependency diagnostics service is registered."""
    _, registrations = await _setup_services(monkeypatch)

    assert "dependency_diagnostics" in registrations


@pytest.mark.asyncio
async def test_dependency_diagnostics_returns_last_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Service returns dependency diagnostics from the last result."""
    hass, registrations = await _setup_services(monkeypatch)

    hass.data[DOMAIN] = {
        DATA_LAST_RESULT: {
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
        },
    }

    response = await registrations["dependency_diagnostics"](
        MagicMock()
    )

    assert response == {
        "affected_entities": 4,
        "unavailable": 2,
        "unknown": 2,
        "critical": 1,
        "high": 1,
        "medium": 1,
        "low": 1,
        "max_impact_score": 55,
    }


@pytest.mark.asyncio
async def test_dependency_diagnostics_without_result_returns_empty_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Service exposes a stable empty summary before an inspection."""
    _, registrations = await _setup_services(monkeypatch)

    response = await registrations["dependency_diagnostics"](
        MagicMock()
    )

    assert response == {
        "affected_entities": 0,
        "unavailable": 0,
        "unknown": 0,
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "max_impact_score": 0,
    }


@pytest.mark.asyncio
async def test_dependency_diagnostics_handles_invalid_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Service tolerates malformed persisted result data."""
    hass, registrations = await _setup_services(monkeypatch)

    hass.data[DOMAIN] = {
        DATA_LAST_RESULT: {
            "dashboard_summary": {
                "dependencies": "invalid",
            },
        },
    }

    response = await registrations["dependency_diagnostics"](
        MagicMock()
    )

    assert response["affected_entities"] == 0
    assert response["max_impact_score"] == 0


def test_dependency_diagnostics_schema_rejects_fields() -> None:
    """Dependency diagnostics service accepts no request fields."""
    assert SERVICE_DEPENDENCY_DIAGNOSTICS_SCHEMA({}) == {}

    with pytest.raises(vol.MultipleInvalid):
        SERVICE_DEPENDENCY_DIAGNOSTICS_SCHEMA(
            {"unexpected": True}
        )


@pytest.mark.asyncio
async def test_dependency_diagnostics_handles_invalid_dashboard_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Service tolerates malformed dashboard summary data."""
    hass, registrations = await _setup_services(monkeypatch)

    hass.data[DOMAIN] = {
        DATA_LAST_RESULT: {
            "dashboard_summary": "invalid",
        },
    }

    response = await registrations["dependency_diagnostics"](
        MagicMock()
    )

    assert response == {
        "affected_entities": 0,
        "unavailable": 0,
        "unknown": 0,
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "max_impact_score": 0,
    }
