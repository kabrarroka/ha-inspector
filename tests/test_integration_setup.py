"""Tests for HA Inspector integration setup helpers."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.ha_inspector import (
    _load_engine,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.ha_inspector.const import (
    DATA_ACKNOWLEDGEMENTS,
    DATA_INSPECTION_HISTORY,
    DATA_REMEDIATION_BASELINES,
    DATA_REMEDIATION_STATE,
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

    remediation_state = MagicMock()
    remediation_state.async_load = AsyncMock()

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
        patch(
            "custom_components.ha_inspector.engine.remediation_state.RemediationStateStore",
            return_value=remediation_state,
        ),
    ):
        assert await async_setup_entry(hass, entry) is True

    restart_history.async_load.assert_awaited_once()
    restart_history.async_record_start.assert_awaited_once()
    inspection_history.async_load.assert_awaited_once()
    acknowledgements.async_load.assert_awaited_once()
    remediation_baselines.async_load.assert_awaited_once()
    remediation_state.async_load.assert_awaited_once()

    assert hass.data[DOMAIN][DATA_RESTART_HISTORY] is restart_history
    assert hass.data[DOMAIN][DATA_INSPECTION_HISTORY] is inspection_history
    assert hass.data[DOMAIN][DATA_ACKNOWLEDGEMENTS] is acknowledgements
    assert (
        hass.data[DOMAIN][DATA_REMEDIATION_BASELINES]
        is remediation_baselines
    )
    assert hass.data[DOMAIN][DATA_REMEDIATION_STATE] is remediation_state

    hass.config_entries.async_forward_entry_setups.assert_awaited_once_with(
        entry,
        PLATFORMS,
    )


async def test_setup_entry_does_not_initialize_histories_twice() -> None:
    existing_restart_history = MagicMock()
    existing_inspection_history = MagicMock()
    existing_acknowledgements = MagicMock()
    existing_remediation_baselines = MagicMock()
    existing_remediation_state = MagicMock()

    hass = MagicMock()
    hass.data = {
        DOMAIN: {
            DATA_RESTART_HISTORY: existing_restart_history,
            DATA_INSPECTION_HISTORY: existing_inspection_history,
            DATA_ACKNOWLEDGEMENTS: existing_acknowledgements,
            DATA_REMEDIATION_BASELINES: existing_remediation_baselines,
            DATA_REMEDIATION_STATE: existing_remediation_state,
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
        patch(
            "custom_components.ha_inspector.engine.remediation_state.RemediationStateStore",
        ) as remediation_state_store_type,
    ):
        assert await async_setup_entry(hass, entry) is True

    restart_history_type.assert_not_called()
    inspection_history_type.assert_not_called()
    acknowledgement_store_type.assert_not_called()
    remediation_baseline_store_type.assert_not_called()
    remediation_state_store_type.assert_not_called()


async def test_unload_entry_unloads_platforms() -> None:
    hass = MagicMock()
    hass.data = {}
    hass.config_entries.async_unload_platforms = AsyncMock(
        return_value=True
    )
    entry = MagicMock()

    assert await async_unload_entry(hass, entry) is True

    hass.config_entries.async_unload_platforms.assert_awaited_once_with(
        entry,
        PLATFORMS,
    )


async def test_setup_entry_does_not_start_periodic_scheduler_by_default() -> None:
    """Periodic scheduling must remain disabled by default."""
    from custom_components.ha_inspector.const import (
        DATA_PERIODIC_RUNNER,
        DATA_PERIODIC_SCHEDULER,
    )

    hass = MagicMock()
    hass.data = {
        DOMAIN: {
            DATA_RESTART_HISTORY: MagicMock(),
            DATA_INSPECTION_HISTORY: MagicMock(),
            DATA_ACKNOWLEDGEMENTS: MagicMock(),
            DATA_REMEDIATION_BASELINES: MagicMock(),
            DATA_REMEDIATION_STATE: MagicMock(),
            DATA_PERIODIC_RUNNER: AsyncMock(),
        }
    }
    hass.config_entries.async_forward_entry_setups = AsyncMock()

    entry = MagicMock()
    entry.options = {}

    with patch(
        "custom_components.ha_inspector.periodic_inspection."
        "PeriodicInspectionScheduler"
    ) as scheduler_type:
        assert await async_setup_entry(hass, entry) is True

    scheduler_type.assert_not_called()

    assert DATA_PERIODIC_SCHEDULER not in hass.data[DOMAIN]

    hass.config_entries.async_forward_entry_setups.assert_awaited_once_with(
        entry,
        PLATFORMS,
    )


async def test_setup_entry_starts_enabled_periodic_scheduler() -> None:
    """Enabled periodic scheduling must use the configured interval and profile."""
    from custom_components.ha_inspector.const import (
        CONF_PERIODIC_INSPECTION_ENABLED,
        CONF_PERIODIC_INSPECTION_INTERVAL,
        CONF_PERIODIC_INSPECTION_PROFILE,
        DATA_PERIODIC_RUNNER,
        DATA_PERIODIC_SCHEDULER,
    )

    runner = AsyncMock(return_value=True)

    hass = MagicMock()
    hass.data = {
        DOMAIN: {
            DATA_RESTART_HISTORY: MagicMock(),
            DATA_INSPECTION_HISTORY: MagicMock(),
            DATA_ACKNOWLEDGEMENTS: MagicMock(),
            DATA_REMEDIATION_BASELINES: MagicMock(),
            DATA_REMEDIATION_STATE: MagicMock(),
            DATA_PERIODIC_RUNNER: runner,
        }
    }
    hass.config_entries.async_forward_entry_setups = AsyncMock()

    entry = MagicMock()
    entry.options = {
        CONF_PERIODIC_INSPECTION_ENABLED: True,
        CONF_PERIODIC_INSPECTION_INTERVAL: 15,
        CONF_PERIODIC_INSPECTION_PROFILE: "system",
    }

    scheduler = MagicMock()

    with patch(
        "custom_components.ha_inspector.periodic_inspection."
        "PeriodicInspectionScheduler",
        return_value=scheduler,
    ) as scheduler_type:
        assert await async_setup_entry(hass, entry) is True

    scheduler_type.assert_called_once()

    assert scheduler_type.call_args.kwargs["interval_minutes"] == 15

    run_inspection = scheduler_type.call_args.kwargs[
        "run_inspection"
    ]

    assert hass.data[DOMAIN][DATA_PERIODIC_SCHEDULER] is scheduler

    scheduler.start.assert_called_once()

    await run_inspection()

    runner.assert_awaited_once_with("system")

    hass.config_entries.async_forward_entry_setups.assert_awaited_once_with(
        entry,
        PLATFORMS,
    )


async def test_unload_entry_stops_periodic_scheduler() -> None:
    """Successful unload must stop and remove the periodic scheduler."""
    from custom_components.ha_inspector.const import (
        DATA_PERIODIC_SCHEDULER,
    )

    scheduler = MagicMock()
    scheduler.stop = AsyncMock()

    hass = MagicMock()
    hass.data = {
        DOMAIN: {
            DATA_PERIODIC_SCHEDULER: scheduler,
        }
    }
    hass.config_entries.async_unload_platforms = AsyncMock(
        return_value=True
    )

    entry = MagicMock()

    assert await async_unload_entry(hass, entry) is True

    hass.config_entries.async_unload_platforms.assert_awaited_once_with(
        entry,
        PLATFORMS,
    )

    scheduler.stop.assert_awaited_once()

    assert DATA_PERIODIC_SCHEDULER not in hass.data[DOMAIN]


async def test_unload_entry_keeps_scheduler_when_platform_unload_fails() -> None:
    """Failed platform unload must leave the scheduler running."""
    from custom_components.ha_inspector.const import (
        DATA_PERIODIC_SCHEDULER,
    )

    scheduler = MagicMock()
    scheduler.stop = AsyncMock()

    hass = MagicMock()
    hass.data = {
        DOMAIN: {
            DATA_PERIODIC_SCHEDULER: scheduler,
        }
    }
    hass.config_entries.async_unload_platforms = AsyncMock(
        return_value=False
    )

    entry = MagicMock()

    assert await async_unload_entry(hass, entry) is False

    hass.config_entries.async_unload_platforms.assert_awaited_once_with(
        entry,
        PLATFORMS,
    )

    scheduler.stop.assert_not_awaited()

    assert hass.data[DOMAIN][DATA_PERIODIC_SCHEDULER] is scheduler


async def test_update_options_reloads_config_entry() -> None:
    """Changing options must request a reload of the config entry."""
    from custom_components.ha_inspector import async_update_options

    hass = MagicMock()
    hass.config_entries.async_reload = AsyncMock()

    entry = MagicMock()
    entry.entry_id = "ha_inspector_test_entry"

    await async_update_options(hass, entry)

    hass.config_entries.async_reload.assert_awaited_once_with(
        "ha_inspector_test_entry"
    )


async def test_setup_entry_registers_options_update_listener() -> None:
    """Setup must register an options listener with unload cleanup."""
    from custom_components.ha_inspector import async_update_options

    hass = MagicMock()
    hass.data = {
        DOMAIN: {
            DATA_RESTART_HISTORY: MagicMock(),
            DATA_INSPECTION_HISTORY: MagicMock(),
            DATA_ACKNOWLEDGEMENTS: MagicMock(),
            DATA_REMEDIATION_BASELINES: MagicMock(),
            DATA_REMEDIATION_STATE: MagicMock(),
        }
    }
    hass.config_entries.async_forward_entry_setups = AsyncMock()

    entry = MagicMock()
    entry.options = {}

    unsubscribe = MagicMock()
    entry.add_update_listener.return_value = unsubscribe

    assert await async_setup_entry(hass, entry) is True

    entry.add_update_listener.assert_called_once_with(
        async_update_options
    )

    entry.async_on_unload.assert_called_once_with(
        unsubscribe
    )
