"""Tests for the Home Assistant backup collector."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.backup.const import DATA_MANAGER

from custom_components.ha_inspector.engine.backup_state import BackupState
from custom_components.ha_inspector.engine.collectors.backups import (
    BackupCollector,
)
from custom_components.ha_inspector.engine.context import InspectionContext

EXPECTED_BACKUP_KEYS = {
    "available",
    "reason",
    "count",
    "latest",
    "oldest",
    "agent_error_count",
    "agent_error_ids",
    "latest_backup_agent_count",
    "latest_backup_agent_ids",
    "latest_backup_failed_addons",
    "latest_backup_failed_folders",
    "latest_backup_failed_agent_ids",
}


@pytest.mark.asyncio
async def test_backup_collector_manager_unavailable() -> None:
    hass = MagicMock()
    hass.data = {}
    context = InspectionContext()

    await BackupCollector().collect(hass, context)

    assert context.backups.as_dict() == {
        "available": False,
        "reason": "Home Assistant backup manager is not available",
        "count": None,
        "latest": None,
        "oldest": None,
        "agent_error_count": 0,
        "agent_error_ids": [],
        "latest_backup_agent_count": None,
        "latest_backup_agent_ids": [],
        "latest_backup_failed_addons": [],
        "latest_backup_failed_folders": [],
        "latest_backup_failed_agent_ids": [],
    }


@pytest.mark.asyncio
async def test_backup_collector_collects_unique_backups() -> None:
    manager = MagicMock()
    manager.async_get_backups = AsyncMock(
        return_value=(
            {
                "backup-1": SimpleNamespace(
                    date="2026-07-01T08:00:00+00:00",
                    agents={"local": SimpleNamespace()},
                ),
                "backup-2": SimpleNamespace(
                    date="2026-08-01T09:30:00+00:00",
                    agents={
                        "cloud": SimpleNamespace(),
                        "local": SimpleNamespace(),
                    },
                    failed_addons=[
                        SimpleNamespace(slug="broken_addon"),
                    ],
                    failed_folders=["media"],
                    failed_agent_ids=[" unavailable_cloud "],
                ),
                "backup-3": SimpleNamespace(
                    date="2026-07-15T12:00:00+00:00",
                    agents={"nas": SimpleNamespace()},
                ),
            },
            {},
        )
    )

    hass = MagicMock()
    hass.data = {DATA_MANAGER: manager}
    context = InspectionContext()

    await BackupCollector().collect(hass, context)

    assert context.backups.as_dict() == {
        "available": True,
        "reason": None,
        "count": 3,
        "latest": "2026-08-01T09:30:00+00:00",
        "oldest": "2026-07-01T08:00:00+00:00",
        "agent_error_count": 0,
        "agent_error_ids": [],
        "latest_backup_agent_count": 2,
        "latest_backup_agent_ids": ["cloud", "local"],
        "latest_backup_failed_addons": ["broken_addon"],
        "latest_backup_failed_folders": ["media"],
        "latest_backup_failed_agent_ids": ["unavailable_cloud"],
    }


@pytest.mark.asyncio
async def test_backup_collector_reports_agent_errors() -> None:
    manager = MagicMock()
    manager.async_get_backups = AsyncMock(
        return_value=(
            {},
            {
                "z_agent": RuntimeError("offline"),
                "a_agent": RuntimeError("unavailable"),
            },
        )
    )

    hass = MagicMock()
    hass.data = {DATA_MANAGER: manager}
    context = InspectionContext()

    await BackupCollector().collect(hass, context)

    assert context.backups.available is True
    assert context.backups.count == 0
    assert context.backups.agent_error_count == 2
    assert context.backups.agent_error_ids == ["a_agent", "z_agent"]


@pytest.mark.asyncio
async def test_backup_collector_handles_manager_error() -> None:
    manager = MagicMock()
    manager.async_get_backups = AsyncMock(
        side_effect=RuntimeError("boom")
    )

    hass = MagicMock()
    hass.data = {DATA_MANAGER: manager}
    context = InspectionContext()

    await BackupCollector().collect(hass, context)

    assert context.backups.as_dict() == {
        "available": False,
        "reason": "Backup inventory could not be read: RuntimeError",
        "count": None,
        "latest": None,
        "oldest": None,
        "agent_error_count": 0,
        "agent_error_ids": [],
        "latest_backup_agent_count": None,
        "latest_backup_agent_ids": [],
        "latest_backup_failed_addons": [],
        "latest_backup_failed_folders": [],
        "latest_backup_failed_agent_ids": [],
    }


@pytest.mark.asyncio
async def test_backup_collector_contract_keys_are_stable() -> None:
    collector = BackupCollector()

    absent_hass = MagicMock()
    absent_hass.data = {}
    absent_context = InspectionContext()
    await collector.collect(absent_hass, absent_context)

    error_manager = MagicMock()
    error_manager.async_get_backups = AsyncMock(
        side_effect=RuntimeError("boom")
    )
    error_hass = MagicMock()
    error_hass.data = {DATA_MANAGER: error_manager}
    error_context = InspectionContext()
    await collector.collect(error_hass, error_context)

    empty_manager = MagicMock()
    empty_manager.async_get_backups = AsyncMock(return_value=({}, {}))
    empty_hass = MagicMock()
    empty_hass.data = {DATA_MANAGER: empty_manager}
    empty_context = InspectionContext()
    await collector.collect(empty_hass, empty_context)

    assert set(absent_context.backups.as_dict()) == EXPECTED_BACKUP_KEYS
    assert set(error_context.backups.as_dict()) == EXPECTED_BACKUP_KEYS
    assert set(empty_context.backups.as_dict()) == EXPECTED_BACKUP_KEYS


@pytest.mark.asyncio
async def test_backup_collector_base_state_lists_are_not_shared() -> None:
    absent_hass = MagicMock()
    absent_hass.data = {}
    absent_context = InspectionContext()
    await BackupCollector().collect(absent_hass, absent_context)

    error_manager = MagicMock()
    error_manager.async_get_backups = AsyncMock(
        side_effect=RuntimeError("boom")
    )
    error_hass = MagicMock()
    error_hass.data = {DATA_MANAGER: error_manager}
    error_context = InspectionContext()
    await BackupCollector().collect(error_hass, error_context)

    absent_context.backups.agent_error_ids.append("mutated")
    absent_context.backups.latest_backup_agent_ids.append("mutated")
    absent_context.backups.latest_backup_failed_addons.append("mutated")
    absent_context.backups.latest_backup_failed_folders.append("mutated")
    absent_context.backups.latest_backup_failed_agent_ids.append("mutated")

    assert error_context.backups.agent_error_ids == []
    assert error_context.backups.latest_backup_agent_ids == []
    assert error_context.backups.latest_backup_failed_addons == []
    assert error_context.backups.latest_backup_failed_folders == []
    assert error_context.backups.latest_backup_failed_agent_ids == []

@pytest.mark.asyncio
async def test_backup_collector_replaces_previous_state() -> None:
    """Ensure stale backup state does not survive a new collection."""
    manager = MagicMock()
    manager.async_get_backups = AsyncMock(return_value=({}, {}))

    hass = MagicMock()
    hass.data = {DATA_MANAGER: manager}

    context = InspectionContext(
        backups=BackupState(
            available=True,
            count=99,
            agent_error_ids=["stale"],
        )
    )

    await BackupCollector().collect(hass, context)

    assert set(context.backups.as_dict()) == EXPECTED_BACKUP_KEYS
    assert "legacy_key" not in context.backups.as_dict()
    assert "obsolete_data" not in context.backups.as_dict()

    assert context.backups.as_dict() == {
        "available": True,
        "reason": None,
        "count": 0,
        "latest": None,
        "oldest": None,
        "agent_error_count": 0,
        "agent_error_ids": [],
        "latest_backup_agent_count": 0,
        "latest_backup_agent_ids": [],
        "latest_backup_failed_addons": [],
        "latest_backup_failed_folders": [],
        "latest_backup_failed_agent_ids": [],
    }