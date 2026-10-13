"""Tests for per-entity remediation summaries."""

from __future__ import annotations

import math

import pytest

from custom_components.ha_inspector.engine.remediation_entity_summary import (
    remediation_entity_summaries,
)
from custom_components.ha_inspector.engine.remediation_plans import (
    RemediationProgress,
)
from custom_components.ha_inspector.engine.remediation_stalled import (
    DEFAULT_STALLED_THRESHOLD_SECONDS,
)


def make_progress(
    entity_id: str = "sensor.example",
    status: str = "pending",
    *,
    new_reference_count: int = 0,
) -> RemediationProgress:
    """Build remediation progress for summary tests."""
    return RemediationProgress(
        entity_id=entity_id,
        status=status,
        total_action_count=5,
        completed_action_count=2,
        remaining_action_count=3,
        new_reference_count=new_reference_count,
    )


def test_empty_progress_returns_empty_tuple() -> None:
    """Empty remediation progress produces no summaries."""
    assert remediation_entity_summaries([], {}) == ()


def test_summaries_are_sorted_by_entity_id() -> None:
    """Summaries use deterministic entity-id ordering."""
    progress = [
        make_progress("sensor.z"),
        make_progress("sensor.a"),
    ]

    summaries = remediation_entity_summaries(progress, {})

    assert [item["entity_id"] for item in summaries] == [
        "sensor.a",
        "sensor.z",
    ]


def test_pending_remediation_has_low_urgency() -> None:
    """Recent pending remediation is not stalled."""
    progress = make_progress()
    age = DEFAULT_STALLED_THRESHOLD_SECONDS - 1

    summary = remediation_entity_summaries(
        [progress],
        {progress.entity_id: age},
    )[0]

    assert summary["status"] == "pending"
    assert summary["age_seconds"] == age
    assert summary["stalled"] is False
    assert summary["urgency"] == "low"


def test_stalled_remediation_has_medium_urgency() -> None:
    """Stalled remediation without new references has medium urgency."""
    progress = make_progress(status="in_progress")
    age = DEFAULT_STALLED_THRESHOLD_SECONDS

    summary = remediation_entity_summaries(
        [progress],
        {progress.entity_id: age},
    )[0]

    assert summary["stalled"] is True
    assert summary["urgency"] == "medium"


def test_stalled_remediation_with_new_references_has_high_urgency() -> None:
    """Stalled remediation with new references has high urgency."""
    progress = make_progress(
        status="in_progress",
        new_reference_count=2,
    )

    summary = remediation_entity_summaries(
        [progress],
        {
            progress.entity_id:
                DEFAULT_STALLED_THRESHOLD_SECONDS + 1
        },
    )[0]

    assert summary["stalled"] is True
    assert summary["urgency"] == "high"
    assert summary["new_reference_count"] == 2


def test_resolved_remediation_has_no_urgency() -> None:
    """Resolved remediation is never stalled."""
    progress = make_progress(status="resolved")

    summary = remediation_entity_summaries(
        [progress],
        {
            progress.entity_id:
                DEFAULT_STALLED_THRESHOLD_SECONDS * 2
        },
    )[0]

    assert summary["status"] == "resolved"
    assert summary["stalled"] is False
    assert summary["urgency"] == "none"


def test_missing_age_is_preserved() -> None:
    """Unknown remediation age remains None."""
    progress = make_progress()

    summary = remediation_entity_summaries(
        [progress],
        {},
    )[0]

    assert summary["age_seconds"] is None
    assert summary["stalled"] is False
    assert summary["urgency"] == "low"


def test_custom_threshold_controls_classification() -> None:
    """Custom thresholds control stalled and urgency values."""
    progress = make_progress(status="in_progress")

    summary = remediation_entity_summaries(
        [progress],
        {progress.entity_id: 100.0},
        threshold_seconds=100.0,
    )[0]

    assert summary["stalled"] is True
    assert summary["urgency"] == "medium"


def test_invalid_threshold_is_rejected() -> None:
    """Invalid stalled thresholds are rejected."""
    progress = make_progress()

    for threshold in (
        -1.0,
        math.nan,
        math.inf,
        -math.inf,
        True,
    ):
        with pytest.raises(
            ValueError,
            match="Stalled remediation threshold",
        ):
            remediation_entity_summaries(
                [progress],
                {},
                threshold_seconds=threshold,
            )


def test_progress_counters_are_preserved() -> None:
    """Entity summaries preserve existing progress counters."""
    progress = make_progress(new_reference_count=2)

    summary = remediation_entity_summaries(
        [progress],
        {},
    )[0]

    assert summary["total_action_count"] == 5
    assert summary["completed_action_count"] == 2
    assert summary["remaining_action_count"] == 3
    assert summary["new_reference_count"] == 2


def test_input_progress_is_not_modified() -> None:
    """Building summaries does not mutate progress objects."""
    progress = make_progress()
    original = progress

    remediation_entity_summaries(
        [progress],
        {progress.entity_id: 100.0},
    )

    assert progress == original
