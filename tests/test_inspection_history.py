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
            "inspection_scope": None,
            "collectors_failed": None,
            "findings": None,
            "remediation": {
                "tracked_entities": 0,
                "pending": 0,
                "in_progress": 0,
                "resolved": 0,
                "total_actions": 0,
                "completed_actions": 0,
                "remaining_actions": 0,
                "new_references": 0,
                "resolved_items": [],
                "new_reference_items": [],
            },
        }
    ]

    assert entries[0]["findings"] is None
    history._store.async_save.assert_awaited_once()



@pytest.mark.asyncio
async def test_add_persists_compact_findings() -> None:
    """Persist finding identities and severities without their details."""
    history = InspectionHistory(MagicMock())
    history._store.async_save = AsyncMock()

    result = _result()
    result["findings"] = [
        {
            "id": "DISK_FREE_SPACE",
            "severity": "critical",
            "title": "Low disk space",
            "description": "Disk space is running low",
            "data": {"free_bytes": 100},
        },
        {
            "id": "UNAVAILABLE_ENTITIES",
            "severity": "warning",
            "title": "Unavailable entities",
        },
    ]

    await history.async_add(result)

    assert history.entries()[0]["findings"] == [
        {"id": "DISK_FREE_SPACE", "severity": "critical"},
        {"id": "UNAVAILABLE_ENTITIES", "severity": "warning"},
    ]
    history._store.async_save.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_normalizes_invalid_findings() -> None:
    """Invalid findings are excluded from compact history."""
    history = InspectionHistory(MagicMock())
    history._store.async_save = AsyncMock()

    result = _result()
    result["findings"] = [
        None,
        "invalid",
        123,
        {},
        {"id": "", "severity": "warning"},
        {"id": "MISSING_SEVERITY"},
        {"id": "EMPTY_SEVERITY", "severity": ""},
        {"id": 123, "severity": "warning"},
        {"id": "INVALID_SEVERITY", "severity": 123},
        {"id": "VALID_FINDING", "severity": "warning"},
    ]

    await history.async_add(result)

    assert history.entries()[0]["findings"] is None

    result["findings"] = "invalid"
    await history.async_add(result)

    assert history.entries()[1]["findings"] is None


@pytest.mark.asyncio
async def test_add_persists_collector_failure_count() -> None:
    """Persist collector failures without assuming missing data means zero."""
    history = InspectionHistory(MagicMock())
    history._store.async_save = AsyncMock()

    result = _result()
    result["metadata"]["collectors_failed"] = 2

    await history.async_add(result)

    assert history.entries()[0]["collectors_failed"] == 2

    result["metadata"]["collectors_failed"] = 0
    await history.async_add(result)

    assert history.entries()[1]["collectors_failed"] == 0

    del result["metadata"]["collectors_failed"]
    await history.async_add(result)

    assert history.entries()[2]["collectors_failed"] is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "value",
    [
        -1,
        True,
        False,
        "2",
        1.5,
        [],
        {},
    ],
)
async def test_add_normalizes_invalid_collector_failures(
    value: object,
) -> None:
    """Invalid collector failure counts are treated as unknown."""
    history = InspectionHistory(MagicMock())
    history._store.async_save = AsyncMock()

    result = _result()
    result["metadata"]["collectors_failed"] = value

    await history.async_add(result)

    assert history.entries()[0]["collectors_failed"] is None

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
async def test_load_preserves_legacy_entries_without_findings() -> None:
    """Legacy history entries retain their unknown finding state."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(
        return_value={
            "entries": [
                {
                    "score": 90,
                    "profile": "quick",
                    "inspection_scope": "legacy-scope",
                },
            ],
        }
    )

    await history.async_load()

    entries = history.entries()

    assert len(entries) == 1
    assert entries[0]["score"] == 90
    assert "findings" not in entries[0]

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


@pytest.mark.asyncio
async def test_domain_trends_use_persisted_entries() -> None:
    """Inspection history exposes domain health trend analysis."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(
        return_value={
            "entries": [
                {
                    "domain_health": {
                        "storage": {
                            "health": {
                                "score": 70,
                            }
                        },
                        "system": {
                            "health": {
                                "score": 95,
                            }
                        },
                    }
                },
                {
                    "domain_health": {
                        "storage": {
                            "health": {
                                "score": 90,
                            }
                        },
                        "system": {
                            "health": {
                                "score": 80,
                            }
                        },
                    }
                },
            ]
        }
    )

    await history.async_load()

    trends = history.domain_trends()

    assert trends["storage"].trend.direction == "improving"
    assert trends["storage"].trend.delta == 20
    assert trends["system"].trend.direction == "declining"
    assert trends["system"].trend.delta == -15


@pytest.mark.asyncio
async def test_domain_trends_handle_empty_history() -> None:
    """Empty persisted history produces no domain trends."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(return_value=None)

    await history.async_load()

    assert history.domain_trends() == {}


@pytest.mark.asyncio
async def test_latest_health_change_uses_persisted_entries() -> None:
    """Inspection history exposes latest health change detection."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(
        return_value={
            "entries": [
                {"score": 90},
                {"score": 85},
                {"score": 70},
            ]
        }
    )

    await history.async_load()

    change = history.latest_health_change()

    assert change.kind == "regression"
    assert change.previous_score == 85
    assert change.current_score == 70
    assert change.delta == -15


@pytest.mark.asyncio
async def test_latest_health_change_handles_empty_history() -> None:
    """Empty persisted history produces insufficient change data."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(return_value=None)

    await history.async_load()

    change = history.latest_health_change()

    assert change.kind == "insufficient_data"
    assert change.previous_score is None
    assert change.current_score is None
    assert change.delta is None


@pytest.mark.asyncio
async def test_latest_comparison_uses_two_most_recent_entries() -> None:
    """Inspection history compares the two latest persisted snapshots."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(
        return_value={
            "entries": [
                {
                    "score": 70,
                    "status": "warning",
                    "total_findings": 6,
                },
                {
                    "score": 80,
                    "status": "warning",
                    "total_findings": 4,
                },
                {
                    "score": 95,
                    "status": "healthy",
                    "total_findings": 1,
                },
            ]
        }
    )

    await history.async_load()

    comparison = history.latest_comparison()

    assert comparison is not None
    assert comparison.previous_score == 80
    assert comparison.current_score == 95
    assert comparison.score_delta == 15
    assert comparison.previous_findings == 4
    assert comparison.current_findings == 1
    assert comparison.findings_delta == -3


@pytest.mark.asyncio
async def test_latest_comparison_requires_two_entries() -> None:
    """Historical comparison requires at least two snapshots."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(
        return_value={
            "entries": [
                {
                    "score": 90,
                }
            ]
        }
    )

    await history.async_load()

    assert history.latest_comparison() is None


@pytest.mark.asyncio
async def test_latest_domain_comparisons_use_two_most_recent_entries() -> None:
    """Inspection history compares domains in the two latest snapshots."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(
        return_value={
            "entries": [
                {
                    "domain_health": {
                        "storage": {
                            "health": {
                                "score": 60,
                                "status": "warning",
                            }
                        }
                    }
                },
                {
                    "domain_health": {
                        "storage": {
                            "health": {
                                "score": 70,
                                "status": "warning",
                            }
                        }
                    }
                },
                {
                    "domain_health": {
                        "storage": {
                            "health": {
                                "score": 90,
                                "status": "excellent",
                            }
                        }
                    }
                },
            ]
        }
    )

    await history.async_load()

    comparisons = history.latest_domain_comparisons()

    assert comparisons is not None
    assert comparisons["storage"].previous_score == 70
    assert comparisons["storage"].current_score == 90
    assert comparisons["storage"].score_delta == 20


@pytest.mark.asyncio
async def test_latest_domain_comparisons_require_two_entries() -> None:
    """Domain comparison requires at least two persisted snapshots."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(
        return_value={
            "entries": [
                {
                    "domain_health": {},
                }
            ]
        }
    )

    await history.async_load()

    assert history.latest_domain_comparisons() is None


@pytest.mark.asyncio
async def test_add_persists_compact_remediation_history() -> None:
    """History persists compact remediation lifecycle state."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(return_value=None)
    history._store.async_save = AsyncMock()

    result = _result()
    result["remediation_progress"] = {
        "tracked_entities": 3,
        "pending": 1,
        "in_progress": 1,
        "resolved": 1,
        "total_actions": 5,
        "completed_actions": 2,
        "remaining_actions": 3,
        "new_references": 1,
        "entities": [
            {
                "entity_id": "sensor.should_not_be_persisted_here",
                "status": "in_progress",
            }
        ],
    }
    result["resolved_remediation_items"] = (
        {
            "entity_id": "sensor.resolved",
            "completed_action_count": 2,
        },
    )
    result["new_remediation_reference_items"] = (
        {
            "entity_id": "sensor.regressed",
            "new_reference_count": 1,
        },
    )

    await history.async_load()
    await history.async_add(result)

    remediation = history.entries()[0]["remediation"]

    assert remediation == {
        "tracked_entities": 3,
        "pending": 1,
        "in_progress": 1,
        "resolved": 1,
        "total_actions": 5,
        "completed_actions": 2,
        "remaining_actions": 3,
        "new_references": 1,
        "resolved_items": [
            {
                "entity_id": "sensor.resolved",
                "completed_action_count": 2,
            }
        ],
        "new_reference_items": [
            {
                "entity_id": "sensor.regressed",
                "new_reference_count": 1,
            }
        ],
    }
    assert "entities" not in remediation


@pytest.mark.asyncio
async def test_add_normalizes_missing_remediation_history() -> None:
    """History supports inspection results without remediation lifecycle data."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(return_value=None)
    history._store.async_save = AsyncMock()

    await history.async_load()
    await history.async_add(_result())

    assert history.entries()[0]["remediation"] == {
        "tracked_entities": 0,
        "pending": 0,
        "in_progress": 0,
        "resolved": 0,
        "total_actions": 0,
        "completed_actions": 0,
        "remaining_actions": 0,
        "new_references": 0,
        "resolved_items": [],
        "new_reference_items": [],
    }


@pytest.mark.asyncio
async def test_latest_remediation_comparison_uses_two_most_recent_entries() -> None:
    """History compares remediation state from the latest two entries."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(
        return_value={
            "entries": [
                {
                    "remediation": {
                        "tracked_entities": 5,
                        "pending": 4,
                        "in_progress": 1,
                        "resolved": 0,
                        "completed_actions": 1,
                        "remaining_actions": 6,
                        "new_references": 0,
                    }
                },
                {
                    "remediation": {
                        "tracked_entities": 4,
                        "pending": 1,
                        "in_progress": 1,
                        "resolved": 2,
                        "completed_actions": 4,
                        "remaining_actions": 2,
                        "new_references": 1,
                    }
                },
            ]
        }
    )

    await history.async_load()

    comparison = history.latest_remediation_comparison()

    assert comparison is not None
    assert comparison.previous_tracked_entities == 5
    assert comparison.current_tracked_entities == 4
    assert comparison.tracked_entities_delta == -1
    assert comparison.previous_resolved == 0
    assert comparison.current_resolved == 2
    assert comparison.resolved_delta == 2
    assert comparison.completed_actions_delta == 3
    assert comparison.remaining_actions_delta == -4
    assert comparison.new_references_delta == 1


@pytest.mark.asyncio
async def test_latest_remediation_comparison_requires_two_entries() -> None:
    """Remediation comparison requires two persisted inspections."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(
        return_value={
            "entries": [
                {
                    "remediation": {
                        "tracked_entities": 1,
                        "pending": 1,
                    }
                }
            ]
        }
    )

    await history.async_load()

    assert history.latest_remediation_comparison() is None


@pytest.mark.asyncio
async def test_add_normalizes_invalid_remediation_progress() -> None:
    """History normalizes malformed remediation progress data."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(return_value=None)
    history._store.async_save = AsyncMock()

    result = _result()
    result["remediation_progress"] = "invalid"

    await history.async_load()
    await history.async_add(result)

    assert history.entries()[0]["remediation"] == {
        "tracked_entities": 0,
        "pending": 0,
        "in_progress": 0,
        "resolved": 0,
        "total_actions": 0,
        "completed_actions": 0,
        "remaining_actions": 0,
        "new_references": 0,
        "resolved_items": [],
        "new_reference_items": [],
    }


def test_remediation_comparison_with_current_result() -> None:
    """History compares its latest remediation state with a current result."""
    history = InspectionHistory(MagicMock())
    history._entries = [
        {
            "remediation": {
                "tracked_entities": 2,
                "pending": 1,
                "in_progress": 1,
                "resolved": 0,
                "completed_actions": 0,
                "remaining_actions": 2,
                "new_references": 0,
            }
        }
    ]

    current = {
        "remediation_progress": {
            "tracked_entities": 2,
            "pending": 0,
            "in_progress": 1,
            "resolved": 1,
            "total_actions": 2,
            "completed_actions": 1,
            "remaining_actions": 1,
            "new_references": 0,
            "entities": [],
        },
        "resolved_remediation_items": [],
        "new_remediation_reference_items": [],
    }

    comparison = history.remediation_comparison_with(current)

    assert comparison is not None
    assert comparison.resolved_delta == 1
    assert comparison.completed_actions_delta == 1
    assert comparison.remaining_actions_delta == -1


def test_remediation_comparison_with_requires_history() -> None:
    """Current remediation comparison requires a previous inspection."""
    history = InspectionHistory(MagicMock())

    assert history.remediation_comparison_with({}) is None



def test_latest_finding_deltas_without_enough_history() -> None:
    """Finding comparison requires two persisted inspections."""
    history = InspectionHistory(MagicMock())

    assert history.latest_finding_deltas() is None


def test_latest_finding_deltas_detects_changes() -> None:
    """Compare findings from the two latest history entries."""
    history = InspectionHistory(MagicMock())

    history._entries = [
        {
            "profile": "quick",
            "inspection_scope": "same-scope",
            "collectors_failed": 0,
            "findings": [
                {"id": "RESOLVED", "severity": "warning"},
                {"id": "PERSISTENT", "severity": "info"},
            ],
        },
        {
            "profile": "quick",
            "inspection_scope": "same-scope",
            "collectors_failed": 0,
            "findings": [
                {"id": "ADDED", "severity": "error"},
                {"id": "PERSISTENT", "severity": "info"},
            ],
        },
    ]

    comparison = history.latest_finding_deltas()

    assert comparison is not None
    assert comparison.added == (
        {"id": "ADDED", "severity": "error"},
    )
    assert comparison.resolved == (
        {"id": "RESOLVED", "severity": "warning"},
    )
    assert comparison.persistent == (
        {"id": "PERSISTENT", "severity": "info"},
    )
    assert comparison.severity_changed == ()


def test_finding_deltas_with_requires_history() -> None:
    """Current finding comparison requires a previous inspection."""
    history = InspectionHistory(MagicMock())

    assert history.finding_deltas_with({}) is None


def test_finding_deltas_with_detects_changes() -> None:
    """Compare current findings with the latest persisted inspection."""
    history = InspectionHistory(MagicMock())

    history._entries = [
        {
            "profile": "quick",
            "inspection_scope": "same-scope",
            "collectors_failed": 0,
            "findings": [
                {"id": "RESOLVED", "severity": "warning"},
                {"id": "PERSISTENT", "severity": "info"},
            ],
        }
    ]

    current_result = {
        "metadata": {
            "profile": "quick",
            "inspection_scope": "same-scope",
            "collectors_failed": 0,
        },
        "findings": [
            {"id": "ADDED", "severity": "error"},
            {"id": "PERSISTENT", "severity": "info"},
        ],
    }

    previous_entries = [
        {
            **entry,
            "findings": [
                finding.copy()
                for finding in entry["findings"]
            ],
        }
        for entry in history._entries
    ]

    comparison = history.finding_deltas_with(current_result)

    assert comparison is not None
    assert comparison.added == (
        {"id": "ADDED", "severity": "error"},
    )
    assert comparison.resolved == (
        {"id": "RESOLVED", "severity": "warning"},
    )
    assert comparison.persistent == (
        {"id": "PERSISTENT", "severity": "info"},
    )
    assert comparison.severity_changed == ()

    assert history._entries == previous_entries
    assert len(history._entries) == 1


@pytest.mark.asyncio
async def test_finding_deltas_with_real_history() -> None:
    """Detect finding changes across two persisted inspections."""
    history = InspectionHistory(MagicMock())
    history._store.async_load = AsyncMock(return_value=None)
    history._store.async_save = AsyncMock()

    await history.async_load()

    first = _result()
    first["metadata"]["inspection_scope"] = "same-scope"
    first["metadata"]["collectors_failed"] = 0
    first["findings"] = [
        {"id": "RESOLVED", "severity": "warning"},
        {"id": "PERSISTENT", "severity": "info"},
    ]

    assert history.finding_deltas_with(first) is None

    await history.async_add(first)

    second = _result()
    second["metadata"]["inspection_scope"] = "same-scope"
    second["metadata"]["collectors_failed"] = 0
    second["findings"] = [
        {"id": "ADDED", "severity": "error"},
        {"id": "PERSISTENT", "severity": "info"},
    ]

    before = history.entries()
    comparison = history.finding_deltas_with(second)

    assert comparison is not None
    assert comparison.added == (
        {"id": "ADDED", "severity": "error"},
    )
    assert comparison.resolved == (
        {"id": "RESOLVED", "severity": "warning"},
    )
    assert comparison.persistent == (
        {"id": "PERSISTENT", "severity": "info"},
    )
    assert comparison.severity_changed == ()

    assert history.entries() == before
    assert len(history.entries()) == 1

    await history.async_add(second)

    assert len(history.entries()) == 2
    assert history.latest_finding_deltas() == comparison



@pytest.mark.asyncio
async def test_incomplete_findings_never_produce_false_resolutions() -> None:
    """Incomplete inspection findings must not imply resolved problems."""
    history = InspectionHistory(MagicMock())
    history._store.async_save = AsyncMock()

    previous = _result()
    previous["metadata"] = {
        "profile": "quick",
        "inspection_scope": "same-scope",
        "collectors_failed": 0,
    }
    previous["findings"] = [
        {"id": "EXISTING_PROBLEM", "severity": "warning"},
    ]
    await history.async_add(previous)

    current = _result()
    current["metadata"] = dict(previous["metadata"])
    current["findings"] = [
        {"id": "VALID_FINDING", "severity": "warning"},
        {"id": "BROKEN_FINDING"},
    ]

    assert history.finding_deltas_with(current) is None

    current["findings"] = []
    deltas = history.finding_deltas_with(current)

    assert deltas is not None
    assert deltas.resolved == (
        {"id": "EXISTING_PROBLEM", "severity": "warning"},
    )
