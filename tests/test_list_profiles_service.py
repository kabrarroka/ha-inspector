"""Tests for the list_profiles service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ha_inspector import async_setup
from custom_components.ha_inspector.const import DOMAIN


@pytest.mark.asyncio
async def test_list_profiles_service_is_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that the list_profiles service is registered."""
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


@pytest.mark.asyncio
async def test_list_profiles_service_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test the response returned by list_profiles."""
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

    handler = registrations["list_profiles"]

    response = await handler(MagicMock())

    profiles = response["profiles"]

    assert profiles
    assert [profile["profile_id"] for profile in profiles] == sorted(
        profile["profile_id"] for profile in profiles
    )

    for profile in profiles:
        assert set(profile) == {
            "profile_id",
            "title",
            "description",
        }
        assert isinstance(profile["profile_id"], str)
        assert isinstance(profile["title"], str)
        assert isinstance(profile["description"], str)


@pytest.mark.asyncio
async def test_list_profiles_contains_builtin_profiles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that the built-in profiles are returned."""
    inspector_type = MagicMock()
    registry = MagicMock()

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

    response = await registrations["list_profiles"](MagicMock())

    profile_ids = {
        profile["profile_id"]
        for profile in response["profiles"]
    }

    assert profile_ids == {
        "entities",
        "full",
        "integrations",
        "quick",
        "recorder",
        "storage",
        "system",
    }

@pytest.mark.asyncio
async def test_list_profiles_uses_home_assistant_language(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """List profiles should use the Home Assistant language."""
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

    response = await registrations["list_profiles"](MagicMock())

    profiles = {
        profile["profile_id"]: profile
        for profile in response["profiles"]
    }

    assert profiles["quick"]["title"] == "Inspección rápida"
    assert profiles["system"]["title"] == "Inspección del sistema"
