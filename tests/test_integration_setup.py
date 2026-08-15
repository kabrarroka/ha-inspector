"""Tests for HA Inspector integration setup helpers."""

from __future__ import annotations

import pytest

from custom_components.ha_inspector import (
    _load_engine,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.ha_inspector.engine.inspector import Inspector
from custom_components.ha_inspector.engine.registry import EngineRegistry


def test_load_engine_returns_inspector_and_registry() -> None:
    inspector_type, registry = _load_engine()

    assert inspector_type is Inspector
    assert isinstance(registry, EngineRegistry)


@pytest.mark.asyncio
async def test_setup_entry_returns_true() -> None:
    assert await async_setup_entry(None, None) is True  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_unload_entry_returns_true() -> None:
    assert await async_unload_entry(None, None) is True  # type: ignore[arg-type]