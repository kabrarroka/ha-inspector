"""Tests for persistent inspection history."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ha_inspector.engine.inspection_history import (
    InspectionHistory,
)


def _result(
    *,
    score: int = 95,
    profile: str | None = "quick",
) -> dict[str, Any]:
    metadata: dict[str, Any] = {}

    if profile is not None:
        metadata["profile"] = profile

    return {
        "started_at": "2026-08-23T08:00:00+00:00",
        "finished_at": "2026-08-23T08:00:01+00:00",
        "duration_seconds": 1.0,
        "score": score,
        "total_findings": 2,
        "summary": {
            "critical": 0,
            "error": 0,
            "warning": 1,
            "info": 1,
        },
        "domain_health": {
            "system": {
                "status": "healthy",
                "score": 100,
            }
        },
        "dashboard_summary": {
            "status": "healthy",
            "score": score,
            "total_findings": 2,
        },
        "metadata": metadata,
        "findings": [
            {"finding_id": "SHOULD_NOT_BE_PERSISTED"},
        ],
    }


@pytest.mark.asyncio
async def test_load_empty_history() -> None:
    """Empty storage produces an empty history."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(return_value=None)

    await history.async_load()

    assert history.entries() == []


@pytest.mark.asyncio
async def test_add_persists_compact_summary() -> None:
    """Adding a result persists only the compact summary."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(return_value=None)
    history._store.async_save = AsyncMock()

    await history.async_load()
    await history.async_add(_result())

    entries = history.entries()

    assert entries == [
        {
            "started_at": "2026-08-23T08:00:00+00:00",
            "finished_at": "2026-08-23T08:00:01+00:00",
            "duration_seconds": 1.0,
            "score": 95,
            "status": "healthy",
            "total_findings": 2,
            "summary": {
                "critical": 0,
                "error": 0,
                "warning": 1,
                "info": 1,
            },
            "domain_health": {
                "system": {
                    "status": "healthy",
                    "score": 100,
                }
            },
            "profile": "quick",
        }
    ]

    assert "findings" not in entries[0]
    history._store.async_save.assert_awaited_once()


@pytest.mark.asyncio
async def test_entries_returns_copy() -> None:
    """Returned history data cannot mutate internal state."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(return_value=None)
    history._store.async_save = AsyncMock()

    await history.async_load()
    await history.async_add(_result())

    entries = history.entries()
    entries[0]["score"] = 1
    entries[0]["domain_health"]["system"]["score"] = 1

    persisted = history.entries()

    assert persisted[0]["score"] == 95
    assert persisted[0]["domain_health"]["system"]["score"] == 100


@pytest.mark.asyncio
async def test_missing_profile_is_supported() -> None:
    """History entries do not require an inspection profile."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(return_value=None)
    history._store.async_save = AsyncMock()

    await history.async_load()
    await history.async_add(_result(profile=None))

    assert history.entries()[0]["profile"] is None


@pytest.mark.asyncio
async def test_history_is_limited_to_100_entries() -> None:
    """Only the most recent history entries are retained."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(return_value=None)
    history._store.async_save = AsyncMock()

    await history.async_load()

    for score in range(105):
        await history.async_add(_result(score=score))

    entries = history.entries()

    assert len(entries) == 100
    assert entries[0]["score"] == 5
    assert entries[-1]["score"] == 104


@pytest.mark.asyncio
async def test_loads_and_limits_persisted_entries() -> None:
    """Loading storage keeps only valid recent entries."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(
        return_value={
            "entries": [
                {"score": score}
                for score in range(105)
            ]
        }
    )

    await history.async_load()

    entries = history.entries()

    assert len(entries) == 100
    assert entries[0]["score"] == 5
    assert entries[-1]["score"] == 104


@pytest.mark.asyncio
async def test_invalid_stored_entries_are_ignored() -> None:
    """Malformed storage data does not break history loading."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(
        return_value={
            "entries": [
                {"score": 90},
                "invalid",
                123,
            ]
        }
    )

    await history.async_load()

    assert history.entries() == [{"score": 90}]


@pytest.mark.asyncio
async def test_load_rejects_non_list_entries() -> None:
    """Malformed entries container produces an empty history."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(
        return_value={
            "entries": "invalid",
        }
    )

    await history.async_load()

    assert history.entries() == []


@pytest.mark.asyncio
async def test_non_mapping_metadata_is_supported() -> None:
    """Malformed result metadata does not break history persistence."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(return_value=None)
    history._store.async_save = AsyncMock()

    result = _result()
    result["metadata"] = "invalid"

    await history.async_load()
    await history.async_add(result)

    assert history.entries()[0]["profile"] is None


@pytest.mark.asyncio
async def test_non_mapping_dashboard_and_domain_health_are_supported() -> None:
    """Malformed optional summaries are normalized to empty mappings."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(return_value=None)
    history._store.async_save = AsyncMock()

    result = _result()
    result["dashboard_summary"] = "invalid"
    result["domain_health"] = "invalid"

    await history.async_load()
    await history.async_add(result)

    entry = history.entries()[0]

    assert entry["status"] is None
    assert entry["domain_health"] == {}


@pytest.mark.asyncio
async def test_score_trend_uses_persisted_entries() -> None:
    """Inspection history exposes health-score trend analysis."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(
        return_value={
            "entries": [
                {"score": 70},
                {"score": 80},
                {"score": 95},
            ]
        }
    )

    await history.async_load()

    trend = history.score_trend()

    assert trend.direction == "improving"
    assert trend.samples == 3
    assert trend.first_score == 70
    assert trend.last_score == 95
    assert trend.delta == 25


@pytest.mark.asyncio
async def test_score_trend_handles_empty_history() -> None:
    """Empty persisted history produces insufficient trend data."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(return_value=None)

    await history.async_load()

    trend = history.score_trend()

    assert trend.direction == "insufficient_data"
    assert trend.samples == 0
