"""Tests for the diagnostic report export service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
import voluptuous as vol

from custom_components.ha_inspector import (
    SERVICE_EXPORT_DIAGNOSTIC_REPORT_SCHEMA,
    async_setup,
)
from custom_components.ha_inspector.const import (
    DATA_LAST_RESULT,
    DOMAIN,
    VERSION,
)


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
async def test_export_diagnostic_report_service_is_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Diagnostic report export service is registered."""
    _, registrations = await _setup_services(monkeypatch)

    assert "export_diagnostic_report" in registrations


@pytest.mark.asyncio
async def test_export_diagnostic_report_uses_last_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Export service builds a report from the last inspection result."""
    hass, registrations = await _setup_services(monkeypatch)

    hass.data[DOMAIN] = {
        DATA_LAST_RESULT: {
            "schema_version": 2,
            "score": 90,
            "findings": [],
            "metadata": {
                "collectors_executed": 2,
            },
        }
    }

    response = await registrations["export_diagnostic_report"](
        MagicMock()
    )

    assert response["schema_version"] == 1
    assert response["generator"] == {
        "name": "HA Inspector",
        "version": VERSION,
    }
    assert response["inspection"]["schema_version"] == 2
    assert response["inspection"]["score"] == 90
    assert response["operational"]["collectors_executed"] == 2


@pytest.mark.asyncio
async def test_export_diagnostic_report_requires_last_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Export fails clearly before any inspection has run."""
    _, registrations = await _setup_services(monkeypatch)

    with pytest.raises(
        RuntimeError,
        match="No HA Inspector inspection result is available",
    ):
        await registrations["export_diagnostic_report"](
            MagicMock()
        )


def test_export_diagnostic_report_schema_rejects_fields() -> None:
    """Export service does not accept request fields."""
    assert SERVICE_EXPORT_DIAGNOSTIC_REPORT_SCHEMA({}) == {}

    with pytest.raises(vol.MultipleInvalid):
        SERVICE_EXPORT_DIAGNOSTIC_REPORT_SCHEMA(
            {"unexpected": True}
        )
