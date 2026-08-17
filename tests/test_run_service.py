"""Tests for the HA Inspector run service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ha_inspector import SERVICE_RUN_SCHEMA, async_setup
from custom_components.ha_inspector.const import DOMAIN


@pytest.mark.asyncio
async def test_run_service_executes_inspection_with_profile() -> None:
    inspector = MagicMock()
    inspector.run = AsyncMock()

    result = MagicMock()
    result.metadata = {}
    result.as_dict.return_value = {
        "findings": [],
        "metadata": result.metadata,
    }

    inspector.run.return_value = result

    inspector_type = MagicMock(return_value=inspector)

    registry = MagicMock()
    registry.collector_ids = ("entities", "system")
    registry.rule_ids = ("CORE_VERSION", "UNAVAILABLE_ENTITIES")
    registry.create_collectors.return_value = ["collector"]
    registry.create_rules.return_value = ["rule"]

    hass = MagicMock()
    hass.async_add_executor_job = AsyncMock(
        return_value=(inspector_type, registry)
    )

    await async_setup(hass, {})

    registrations = {
        call.args[1]: call.args[2]
        for call in hass.services.async_register.call_args_list
        if call.args[0] == DOMAIN
    }

    run_registration = next(
        call
        for call in hass.services.async_register.call_args_list
        if call.args[:2] == (DOMAIN, "run")
    )
    assert run_registration.kwargs["schema"] is SERVICE_RUN_SCHEMA

    service_call = MagicMock()
    service_call.data = {
        "profile": "quick",
    }

    response = await registrations["run"](service_call)

    inspector_type.assert_called_once_with(
        collectors=["collector"],
        rules=["rule"],
    )
    inspector.run.assert_awaited_once()

    assert result.metadata["registry"] == {
        "collectors": ["entities", "system"],
        "rules": ["CORE_VERSION", "UNAVAILABLE_ENTITIES"],
    }
    assert result.metadata["profile"] == "quick"
    assert response == {
        "findings": [],
        "metadata": result.metadata,
    }