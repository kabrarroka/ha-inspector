"""Tests for the info service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ha_inspector import (
    SERVICE_INFO_SCHEMA,
    async_setup,
)
from custom_components.ha_inspector.const import DOMAIN, VERSION


@pytest.mark.asyncio
async def test_info_service_is_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that the info service is registered."""
    inspector_type = MagicMock()
    registry = MagicMock()

    registry.rule_ids = ("RULE_ONE", "RULE_TWO")
    registry.collector_ids = ("collector_one",)

    monkeypatch.setattr(
        "custom_components.ha_inspector._load_engine",
        lambda: (inspector_type, registry),
    )

    hass = MagicMock()
    hass.async_add_executor_job = AsyncMock(
        return_value=(inspector_type, registry)
    )

    result = await async_setup(hass, {})

    assert result is True

    registered_services = [
        call.args[1]
        for call in hass.services.async_register.call_args_list
    ]

    assert "run" in registered_services
    assert "list_profiles" in registered_services
    assert "describe_profile" in registered_services
    assert "info" in registered_services


@pytest.mark.asyncio
async def test_info_service_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test the response returned by the info service."""
    inspector_type = MagicMock()
    registry = MagicMock()

    registry.rule_ids = (
        "RULE_ONE",
        "RULE_TWO",
        "RULE_THREE",
    )
    registry.collector_ids = (
        "collector_one",
        "collector_two",
    )

    monkeypatch.setattr(
        "custom_components.ha_inspector._load_engine",
        lambda: (inspector_type, registry),
    )

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

    response = await registrations["info"](MagicMock())

    assert response["api_version"] == 1
    assert response["engine"] == {
        "profiles": 7,
        "rules": 3,
        "collectors": 2,
    }
    assert response["version"] == VERSION


@pytest.mark.asyncio
async def test_info_service_engine_structure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test the structure returned by the info service."""
    inspector_type = MagicMock()
    registry = MagicMock()

    registry.rule_ids = ("RULE_ONE",)
    registry.collector_ids = ("collector_one",)

    monkeypatch.setattr(
        "custom_components.ha_inspector._load_engine",
        lambda: (inspector_type, registry),
    )

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

    response = await registrations["info"](MagicMock())

    assert set(response) == {
        "version",
        "api_version",
        "engine",
    }

    assert set(response["engine"]) == {
        "profiles",
        "rules",
        "collectors",
    }


@pytest.mark.asyncio
async def test_info_service_counts_are_integers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that the engine counters are integers."""
    inspector_type = MagicMock()
    registry = MagicMock()

    registry.rule_ids = (
        "RULE_ONE",
        "RULE_TWO",
    )
    registry.collector_ids = (
        "collector_one",
        "collector_two",
        "collector_three",
    )

    monkeypatch.setattr(
        "custom_components.ha_inspector._load_engine",
        lambda: (inspector_type, registry),
    )

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

    response = await registrations["info"](MagicMock())

    engine = response["engine"]

    assert isinstance(engine["profiles"], int)
    assert isinstance(engine["rules"], int)
    assert isinstance(engine["collectors"], int)

    assert engine["profiles"] > 0
    assert engine["rules"] > 0
    assert engine["collectors"] > 0

def test_version_matches_manifest() -> None:
    """Test that the integration version matches manifest.json."""
    from json import loads
    from pathlib import Path

    manifest_path = (
        Path(__file__).parents[1]
        / "custom_components"
        / "ha_inspector"
        / "manifest.json"
    )

    manifest = loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["version"] == VERSION

def test_info_schema_rejects_fields() -> None:
    import voluptuous as vol

    with pytest.raises(vol.MultipleInvalid):
        SERVICE_INFO_SCHEMA({"unexpected": True})