"""Tests for the Home Assistant backup collector."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from homeassistant.components.backup.const import DATA_MANAGER

from custom_components.ha_inspector.engine.collectors.backups import (
    BackupCollector,
)
from custom_components.ha_inspector.engine.context import InspectionContext


@pytest.mark.asyncio
async def test_backup_collector_manager_unavailable() -> None:
    hass = MagicMock()
    hass.data = {}
    context = InspectionContext()

    await BackupCollector().collect(hass, context)

    assert context.backups == {
        "available": False,
        "reason": "Home Assistant backup manager is not available",
        "count": None,
        "latest": None,
        "oldest": None,
        "agent_error_count": 0,
        "agent_error_ids": [],
    }


@pytest.mark.asyncio
async def test_backup_collector_collects_unique_backups() -> None:
    manager = MagicMock()
    manager.async_get_backups = AsyncMock(
        return_value=(
            {
                "backup-1": SimpleNamespace(
                    date=datetime(2026, 7, 1, 8, 0, tzinfo=UTC)
                ),
                "backup-2": SimpleNamespace(
                    date=datetime(2026, 8, 1, 9, 30, tzinfo=UTC)
                ),
                "backup-3": SimpleNamespace(
                    date=datetime(2026, 7, 15, 12, 0, tzinfo=UTC)
                ),
            },
            {},
        )
    )

    hass = MagicMock()
    hass.data = {DATA_MANAGER: manager}
    context = InspectionContext()

    await BackupCollector().collect(hass, context)

    assert context.backups == {
        "available": True,
        "reason": None,
        "count": 3,
        "latest": "2026-08-01T09:30:00+00:00",
        "oldest": "2026-07-01T08:00:00+00:00",
        "agent_error_count": 0,
        "agent_error_ids": [],
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

    assert context.backups["available"] is True
    assert context.backups["count"] == 0
    assert context.backups["agent_error_count"] == 2
    assert context.backups["agent_error_ids"] == [
        "a_agent",
        "z_agent",
    ]


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

    assert context.backups["available"] is False
    assert context.backups["count"] is None
    assert context.backups["reason"] == (
        "Backup inventory could not be read: RuntimeError"
    )
