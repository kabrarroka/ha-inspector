"""Tests for HA Inspector integration setup helpers."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ha_inspector import (
    _load_engine,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.ha_inspector.const import PLATFORMS
from custom_components.ha_inspector.engine.inspector import Inspector
from custom_components.ha_inspector.engine.registry import EngineRegistry


def test_load_engine_returns_inspector_and_registry() -> None:
    inspector_type, registry = _load_engine()

    assert inspector_type is Inspector
    assert isinstance(registry, EngineRegistry)


@pytest.mark.asyncio
async def test_setup_entry_forwards_platforms() -> None:
    hass = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    entry = MagicMock()

    assert await async_setup_entry(hass, entry) is True

    hass.config_entries.async_forward_entry_setups.assert_awaited_once_with(
        entry,
        PLATFORMS,
    )


@pytest.mark.asyncio
async def test_unload_entry_unloads_platforms() -> None:
    hass = MagicMock()
    hass.config_entries.async_unload_platforms = AsyncMock(
        return_value=True
    )
    entry = MagicMock()

    assert await async_unload_entry(hass, entry) is True

    hass.config_entries.async_unload_platforms.assert_awaited_once_with(
        entry,
        PLATFORMS,
    )
