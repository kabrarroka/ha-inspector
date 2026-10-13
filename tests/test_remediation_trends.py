"""Tests for remediation lifecycle trend analytics."""

from __future__ import annotations

from typing import Any

from custom_components.ha_inspector.engine.remediation_trends import (
    remediation_lifecycle_trend,
)


def _entry(
    *,
    pending: int = 2,
    in_progress: int = 0,
    resolved: int = 0,
    completed_actions: int = 0,
    remaining_actions: int = 4,
    new_references: int = 0,
) -> dict[str, Any]:
    """Build a compact remediation history entry."""
    return {
        "profile": "full",
        "inspection_scope": "scope-full",
        "remediation": {
            "pending": pending,
            "in_progress": in_progress,
            "resolved": resolved,
            "completed_actions": completed_actions,
            "remaining_actions": remaining_actions,
            "new_references": new_references,
        },
    }


def test_trend_requires_two_samples() -> None:
    """Empty and single-entry histories lack sufficient data."""
    empty = remediation_lifecycle_trend([])

    assert empty.direction == "insufficient_data"
    assert empty.samples == 0
    assert empty.remaining_actions_delta is None

    single = remediation_lifecycle_trend([_entry()])

    assert single.direction == "insufficient_data"
    assert single.samples == 1
    assert single.remaining_actions_delta is None


def test_trend_detects_improvement() -> None:
    """Reducing remaining actions indicates improvement."""
    trend = remediation_lifecycle_trend(
        [
            _entry(
                pending=2,
                remaining_actions=4,
            ),
            _entry(
                pending=1,
                in_progress=1,
                resolved=1,
                completed_actions=2,
                remaining_actions=2,
            ),
        ]
    )

    assert trend.direction == "improving"
    assert trend.samples == 2
    assert trend.pending_delta == -1
    assert trend.resolved_delta == 1
    assert trend.completed_actions_delta == 2
    assert trend.remaining_actions_delta == -2


def test_trend_detects_decline() -> None:
    """Increasing new references indicates deterioration."""
    trend = remediation_lifecycle_trend(
        [
            _entry(),
            _entry(
                new_references=2,
                remaining_actions=5,
            ),
        ]
    )

    assert trend.direction == "declining"
    assert trend.new_references_delta == 2
    assert trend.remaining_actions_delta == 1


def test_trend_detects_stability() -> None:
    """Unchanged remediation counters indicate stability."""
    trend = remediation_lifecycle_trend(
        [
            _entry(),
            _entry(),
        ]
    )

    assert trend.direction == "stable"
    assert trend.samples == 2
    assert trend.pending_delta == 0
    assert trend.remaining_actions_delta == 0
    assert trend.new_references_delta == 0


def test_trend_serializes() -> None:
    """Trend summaries expose JSON-compatible values."""
    trend = remediation_lifecycle_trend(
        [
            _entry(remaining_actions=4),
            _entry(remaining_actions=2),
        ]
    )

    assert trend.as_dict() == {
        "direction": "improving",
        "samples": 2,
        "pending_delta": 0,
        "in_progress_delta": 0,
        "resolved_delta": 0,
        "completed_actions_delta": 0,
        "remaining_actions_delta": -2,
        "new_references_delta": 0,
    }


def test_trend_ignores_invalid_remediation_entries() -> None:
    """Invalid remediation counters must not contribute samples."""
    negative = _entry(remaining_actions=-1)
    boolean = _entry()
    boolean["remediation"]["pending"] = True

    incomplete = _entry()
    del incomplete["remediation"]["resolved"]

    trend = remediation_lifecycle_trend(
        [
            negative,
            boolean,
            incomplete,
            _entry(remaining_actions=4),
            _entry(remaining_actions=2),
        ]
    )

    assert trend.direction == "improving"
    assert trend.samples == 2
    assert trend.remaining_actions_delta == -2


def test_trend_uses_first_and_last_valid_samples() -> None:
    """Trends cover the complete comparable inspection period."""
    trend = remediation_lifecycle_trend(
        [
            _entry(remaining_actions=8),
            _entry(remaining_actions=6),
            _entry(remaining_actions=4),
            _entry(remaining_actions=2),
        ]
    )

    assert trend.direction == "improving"
    assert trend.samples == 4
    assert trend.remaining_actions_delta == -6


def test_trend_does_not_mix_different_profiles() -> None:
    """Inspections from different profiles are not comparable."""
    full = _entry(remaining_actions=6)
    dependencies = _entry(remaining_actions=2)
    dependencies["profile"] = "dependencies"
    dependencies["inspection_scope"] = "scope-dependencies"

    trend = remediation_lifecycle_trend(
        [
            full,
            dependencies,
        ]
    )

    assert trend.direction == "insufficient_data"
    assert trend.samples == 1
    assert trend.remaining_actions_delta is None


def test_trend_prioritizes_new_reference_regression() -> None:
    """New references take priority over reduced remaining actions."""
    trend = remediation_lifecycle_trend(
        [
            _entry(
                remaining_actions=6,
                new_references=0,
            ),
            _entry(
                remaining_actions=3,
                new_references=2,
            ),
        ]
    )

    assert trend.direction == "declining"
    assert trend.remaining_actions_delta == -3
    assert trend.new_references_delta == 2


def test_trend_handles_interleaved_profiles() -> None:
    """Other inspection profiles must not affect the trend."""
    first = _entry(remaining_actions=8)

    unrelated = _entry(remaining_actions=1)
    unrelated["profile"] = "dependencies"
    unrelated["inspection_scope"] = "scope-dependencies"

    last = _entry(remaining_actions=4)

    trend = remediation_lifecycle_trend(
        [
            first,
            unrelated,
            last,
        ]
    )

    assert trend.direction == "improving"
    assert trend.samples == 2
    assert trend.remaining_actions_delta == -4


def test_trend_rejects_invalid_latest_inspection() -> None:
    """An invalid latest inspection must not produce a stale trend."""
    invalid = _entry()
    invalid["remediation"]["remaining_actions"] = None

    trend = remediation_lifecycle_trend(
        [
            _entry(remaining_actions=8),
            _entry(remaining_actions=4),
            invalid,
        ]
    )

    assert trend.direction == "insufficient_data"
    assert trend.remaining_actions_delta is None


def test_trend_does_not_assume_missing_scopes_are_comparable() -> None:
    """Missing inspection scopes cannot establish comparability."""
    first = _entry(remaining_actions=8)
    last = _entry(remaining_actions=4)

    del first["inspection_scope"]
    del last["inspection_scope"]

    trend = remediation_lifecycle_trend(
        [
            first,
            last,
        ]
    )

    assert trend.direction == "insufficient_data"
    assert trend.remaining_actions_delta is None
