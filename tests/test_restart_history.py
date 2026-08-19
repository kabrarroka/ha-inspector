"""Tests for persistent restart history."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ha_inspector.engine.restart_history import (
    RestartHistory,
)


@pytest.mark.asyncio
async def test_restart_history_loads_and_counts(monkeypatch) -> None:
    now = datetime(2026, 8, 19, 8, 0, tzinfo=UTC)

    history = RestartHistory(MagicMock())

    history._store.async_load = AsyncMock(
        return_value={
            "starts": [
                (now - timedelta(hours=12)).isoformat(),
                (now - timedelta(hours=6)).isoformat(),
                now.isoformat(),
            ]
        }
    )

    await history.async_load()

    assert history.restart_counts(now) == (2, 2)


@pytest.mark.asyncio
async def test_restart_history_records_and_saves() -> None:
    now = datetime(2026, 8, 19, 8, 0, tzinfo=UTC)

    history = RestartHistory(MagicMock())
    history._store.async_load = AsyncMock(return_value=None)
    history._store.async_save = AsyncMock()

    await history.async_load()
    await history.async_record_start(now)

    assert history.restart_counts(now) == (0, 0)
    history._store.async_save.assert_awaited_once()


@pytest.mark.asyncio
async def test_restart_history_prunes_old_entries() -> None:
    now = datetime(2026, 8, 19, 8, 0, tzinfo=UTC)

    history = RestartHistory(MagicMock())
    history._store.async_load = AsyncMock(
        return_value={
            "starts": [
                (now - timedelta(days=31)).isoformat(),
                (now - timedelta(days=2)).isoformat(),
            ]
        }
    )

    await history.async_load()

    assert history.restart_counts(now) == (0, 0)



@pytest.mark.asyncio
async def test_restart_history_counts_all_starts_after_baseline_window() -> None:
    now = datetime(2026, 8, 19, 8, 0, tzinfo=UTC)

    history = RestartHistory(MagicMock())
    history._store.async_load = AsyncMock(
        return_value={
            "starts": [
                (now - timedelta(days=8)).isoformat(),
                (now - timedelta(hours=20)).isoformat(),
                (now - timedelta(hours=10)).isoformat(),
                now.isoformat(),
            ]
        }
    )

    await history.async_load()

    assert history.restart_counts(now) == (3, 3)
