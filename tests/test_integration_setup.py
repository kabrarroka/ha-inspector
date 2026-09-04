"""Tests for HA Inspector integration setup helpers."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.ha_inspector import (
    _load_engine,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.ha_inspector.const import (
    DATA_ACKNOWLEDGEMENTS,
    DATA_INSPECTION_HISTORY,
    DATA_REMEDIATION_BASELINES,
    DATA_RESTART_HISTORY,
    DOMAIN,
    PLATFORMS,
)
from custom_components.ha_inspector.engine.inspector import Inspector
from custom_components.ha_inspector.engine.registry import EngineRegistry


def test_load_engine_returns_inspector_and_registry() -> None:
    inspector_type, registry = _load_engine()

    assert inspector_type is Inspector
    assert isinstance(registry, EngineRegistry)


@pytest.mark.asyncio
async def test_setup_entry_forwards_platforms() -> None:
    hass = MagicMock()
    hass.data = {}
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    entry = MagicMock()

    restart_history = MagicMock()
    restart_history.async_load = AsyncMock()
    restart_history.async_record_start = AsyncMock()

    inspection_history = MagicMock()
    inspection_history.async_load = AsyncMock()

    acknowledgements = MagicMock()
    acknowledgements.async_load = AsyncMock()

    remediation_baselines = MagicMock()
    remediation_baselines.async_load = AsyncMock()

    with (
        patch(
            "custom_components.ha_inspector.engine.restart_history.RestartHistory",
            return_value=restart_history,
        ),
        patch(
            "custom_components.ha_inspector.engine.inspection_history.InspectionHistory",
            return_value=inspection_history,
        ),
        patch(
            "custom_components.ha_inspector.engine.acknowledgements.AcknowledgementStore",
            return_value=acknowledgements,
        ),
        patch(
            "custom_components.ha_inspector.engine.remediation_baselines.RemediationBaselineStore",
            return_value=remediation_baselines,
        ),
    ):
        assert await async_setup_entry(hass, entry) is True

    restart_history.async_load.assert_awaited_once()
    restart_history.async_record_start.assert_awaited_once()
    inspection_history.async_load.assert_awaited_once()
    acknowledgements.async_load.assert_awaited_once()
    remediation_baselines.async_load.assert_awaited_once()

    assert hass.data[DOMAIN][DATA_RESTART_HISTORY] is restart_history
    assert hass.data[DOMAIN][DATA_INSPECTION_HISTORY] is inspection_history
    assert hass.data[DOMAIN][DATA_ACKNOWLEDGEMENTS] is acknowledgements
    assert (
        hass.data[DOMAIN][DATA_REMEDIATION_BASELINES]
        is remediation_baselines
    )

    hass.config_entries.async_forward_entry_setups.assert_awaited_once_with(
        entry,
        PLATFORMS,
    )


@pytest.mark.asyncio
async def test_setup_entry_does_not_initialize_histories_twice() -> None:
    existing_restart_history = MagicMock()
    existing_inspection_history = MagicMock()
    existing_acknowledgements = MagicMock()
    existing_remediation_baselines = MagicMock()

    hass = MagicMock()
    hass.data = {
        DOMAIN: {
            DATA_RESTART_HISTORY: existing_restart_history,
            DATA_INSPECTION_HISTORY: existing_inspection_history,
            DATA_ACKNOWLEDGEMENTS: existing_acknowledgements,
            DATA_REMEDIATION_BASELINES: existing_remediation_baselines,
        }
    }
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    entry = MagicMock()

    with (
        patch(
            "custom_components.ha_inspector.engine.restart_history.RestartHistory",
        ) as restart_history_type,
        patch(
            "custom_components.ha_inspector.engine.inspection_history.InspectionHistory",
        ) as inspection_history_type,
        patch(
            "custom_components.ha_inspector.engine.acknowledgements.AcknowledgementStore",
        ) as acknowledgement_store_type,
        patch(
            "custom_components.ha_inspector.engine.remediation_baselines.RemediationBaselineStore",
        ) as remediation_baseline_store_type,
    ):
        assert await async_setup_entry(hass, entry) is True

    restart_history_type.assert_not_called()
    inspection_history_type.assert_not_called()
    acknowledgement_store_type.assert_not_called()
    remediation_baseline_store_type.assert_not_called()


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
