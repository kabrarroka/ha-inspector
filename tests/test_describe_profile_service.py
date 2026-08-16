"""Tests for the describe_profile service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ha_inspector import async_setup
from custom_components.ha_inspector.const import DOMAIN
from custom_components.ha_inspector.engine.profiles import (
    InspectionProfileError,
)


@pytest.mark.asyncio
async def test_describe_profile_service_is_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that the describe_profile service is registered."""
    inspector_type = MagicMock()
    registry = MagicMock()

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


@pytest.mark.asyncio
async def test_describe_profile_returns_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that describe_profile returns the requested profile."""
    inspector_type = MagicMock()
    registry = MagicMock()

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

    call = MagicMock()
    call.data = {
        "profile_id": "quick",
    }

    response = await registrations["describe_profile"](call)

    profile = response["profile"]

    assert profile["profile_id"] == "quick"
    assert profile["title"] == "Quick inspection"
    assert profile["description"]
    assert "request" in profile


@pytest.mark.asyncio
async def test_describe_profile_contains_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that describe_profile returns the profile request."""
    inspector_type = MagicMock()
    registry = MagicMock()

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

    call = MagicMock()
    call.data = {
        "profile_id": "storage",
    }

    response = await registrations["describe_profile"](call)

    request = response["profile"]["request"]

    assert "include_rule_ids" in request
    assert request["include_rule_ids"] == [
        "DISK_FREE_SPACE",
    ]


@pytest.mark.asyncio
async def test_describe_profile_unknown_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that an unknown profile raises an error."""
    inspector_type = MagicMock()
    registry = MagicMock()

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

    call = MagicMock()
    call.data = {
        "profile_id": "missing",
    }

    with pytest.raises(
        InspectionProfileError,
        match="Unknown inspection profile",
    ):
        await registrations["describe_profile"](call)

@pytest.mark.asyncio
async def test_describe_profile_uses_home_assistant_language(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Describe profile should use the Home Assistant language."""
    inspector_type = MagicMock()
    registry = MagicMock()

    monkeypatch.setattr(
        "custom_components.ha_inspector._load_engine",
        lambda: (inspector_type, registry),
    )

    hass = MagicMock()
    hass.config.language = "es-ES"
    hass.async_add_executor_job = AsyncMock(
        return_value=(inspector_type, registry)
    )

    await async_setup(hass, {})

    registrations = {
        call.args[1]: call.args[2]
        for call in hass.services.async_register.call_args_list
        if call.args[0] == DOMAIN
    }

    call = MagicMock()
    call.data = {"profile_id": "quick"}

    response = await registrations["describe_profile"](call)

    assert response["profile"]["profile_id"] == "quick"
    assert response["profile"]["title"] == "Inspección rápida"
