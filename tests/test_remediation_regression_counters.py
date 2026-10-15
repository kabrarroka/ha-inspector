"""Tests for historical remediation regression counters."""

from __future__ import annotations

from typing import Any

from custom_components.ha_inspector.engine.remediation_trends import (
    remediation_lifecycle_trend,
)


def _entry(
    remaining: int,
    references: int = 0,
    *,
    scope: str = "scope-full",
) -> dict[str, Any]:
    """Build a comparable remediation history entry."""
    return {
        "inspection_scope": scope,
        "remediation": {
            "pending": 1,
            "in_progress": 0,
            "resolved": 0,
            "completed_actions": 0,
            "remaining_actions": remaining,
            "new_references": references,
        },
    }


def test_regression_counters_require_two_samples() -> None:
    """Insufficient history produces zero regression counts."""
    for entries in ([], [_entry(4)]):
        trend = remediation_lifecycle_trend(entries)

        assert trend.regression_count == 0
        assert trend.remaining_actions_regression_count == 0
        assert trend.new_references_regression_count == 0


def test_regression_counters_detect_remaining_actions_increases() -> None:
    """Count each transition with increased remaining actions."""
    trend = remediation_lifecycle_trend(
        [
            _entry(8),
            _entry(6),
            _entry(9),
            _entry(7),
            _entry(10),
        ]
    )

    assert trend.regression_count == 2
    assert trend.remaining_actions_regression_count == 2
    assert trend.new_references_regression_count == 0


def test_regression_counters_detect_new_references_increases() -> None:
    """Count regressions caused by newly introduced references."""
    trend = remediation_lifecycle_trend(
        [
            _entry(8, 0),
            _entry(7, 2),
            _entry(6, 1),
            _entry(5, 3),
        ]
    )

    assert trend.regression_count == 2
    assert trend.remaining_actions_regression_count == 0
    assert trend.new_references_regression_count == 2


def test_regression_counters_do_not_double_count_transitions() -> None:
    """A transition with both regressions counts only once overall."""
    trend = remediation_lifecycle_trend(
        [
            _entry(4, 0),
            _entry(6, 2),
            _entry(5, 1),
        ]
    )

    assert trend.regression_count == 1
    assert trend.remaining_actions_regression_count == 1
    assert trend.new_references_regression_count == 1


def test_regression_counters_ignore_other_scopes() -> None:
    """Unrelated inspection scopes do not affect regression counts."""
    trend = remediation_lifecycle_trend(
        [
            _entry(8),
            _entry(20, scope="scope-dependencies"),
            _entry(6),
            _entry(9),
        ]
    )

    assert trend.samples == 3
    assert trend.regression_count == 1
    assert trend.remaining_actions_regression_count == 1


def test_regression_counters_ignore_invalid_history() -> None:
    """Malformed remediation history must not introduce regressions."""
    invalid = _entry(100)
    invalid["remediation"] = None

    trend = remediation_lifecycle_trend(
        [
            _entry(8),
            invalid,
            _entry(6),
            _entry(9),
        ]
    )

    assert trend.samples == 3
    assert trend.regression_count == 1


def test_regression_counters_are_serialized() -> None:
    """Regression counters are included in the public trend document."""
    trend = remediation_lifecycle_trend(
        [
            _entry(4, 0),
            _entry(6, 2),
        ]
    )

    document = trend.as_dict()

    assert document["regression_count"] == 1
    assert document["remaining_actions_regression_count"] == 1
    assert document["new_references_regression_count"] == 1
