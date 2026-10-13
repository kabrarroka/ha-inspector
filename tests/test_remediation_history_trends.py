"""Integration tests for remediation lifecycle history trends."""

from __future__ import annotations

from typing import Any

from custom_components.ha_inspector.engine.inspection_history import (
    InspectionHistory,
)


def _entry(
    remaining: int,
    *,
    profile: str = "full",
) -> dict[str, Any]:
    """Build a compact historical inspection."""
    return {
        "profile": profile,
        "inspection_scope": f"scope-{profile}",
        "remediation": {
            "pending": 1,
            "in_progress": 0,
            "resolved": 0,
            "completed_actions": 0,
            "remaining_actions": remaining,
            "new_references": 0,
        },
    }


def _result(
    remaining: int,
    *,
    profile: str = "full",
) -> dict[str, Any]:
    """Build an inspection result before history persistence."""
    return {
        "metadata": {
            "profile": profile,
            "inspection_scope": f"scope-{profile}",
        },
        "remediation_progress": {
            "pending": 1,
            "in_progress": 0,
            "resolved": 0,
            "completed_actions": 0,
            "remaining_actions": remaining,
            "new_references": 0,
        },
    }


def test_remediation_trend_uses_persisted_history() -> None:
    """Stored remediation history exposes lifecycle trends."""
    history = object.__new__(InspectionHistory)
    history._entries = [
        _entry(remaining=8),
        _entry(remaining=6),
        _entry(remaining=4),
    ]

    trend = history.remediation_trend()

    assert trend.direction == "improving"
    assert trend.samples == 3
    assert trend.remaining_actions_delta == -4


def test_remediation_trend_with_includes_current_result() -> None:
    """Current inspection is included without being persisted."""
    history = object.__new__(InspectionHistory)
    history._entries = [
        _entry(remaining=8),
        _entry(remaining=6),
    ]

    trend = history.remediation_trend_with(_result(remaining=4))

    assert trend.direction == "improving"
    assert trend.samples == 3
    assert trend.remaining_actions_delta == -4

    assert len(history.entries()) == 2
    assert history.entries()[-1]["remediation"]["remaining_actions"] == 6


def test_remediation_trend_with_respects_scopes() -> None:
    """Current inspection only compares matching scopes."""
    history = object.__new__(InspectionHistory)
    history._entries = [
        _entry(remaining=8, profile="full"),
        _entry(remaining=6, profile="dependencies"),
    ]

    trend = history.remediation_trend_with(_result(remaining=4, profile="full"))

    assert trend.direction == "improving"
    assert trend.samples == 2
    assert trend.remaining_actions_delta == -4


def test_remediation_trend_with_requires_comparable_history() -> None:
    """One current inspection cannot establish a trend."""
    history = object.__new__(InspectionHistory)
    history._entries = []

    trend = history.remediation_trend_with(_result(remaining=4))

    assert trend.direction == "insufficient_data"
    assert trend.samples == 1
    assert trend.remaining_actions_delta is None


def test_remediation_trend_with_does_not_duplicate_current_inspection() -> None:
    """Calculate the current trend without persisting or duplicating it."""
    history = object.__new__(InspectionHistory)
    history._entries = [
        _entry(remaining=8),
        _entry(remaining=6),
    ]

    current_result = _result(remaining=4)

    first_trend = history.remediation_trend_with(current_result)
    second_trend = history.remediation_trend_with(current_result)

    assert first_trend.direction == "improving"
    assert first_trend.samples == 3
    assert first_trend.remaining_actions_delta == -4

    assert second_trend == first_trend

    stored_entries = history.entries()

    assert len(stored_entries) == 2
    assert stored_entries[0]["remediation"]["remaining_actions"] == 8
    assert stored_entries[1]["remediation"]["remaining_actions"] == 6


def test_remediation_trend_with_excludes_other_scopes() -> None:
    """Only inspections with the same scope contribute to the trend."""
    history = object.__new__(InspectionHistory)
    history._entries = [
        _entry(remaining=10, profile="dependencies"),
        _entry(remaining=8, profile="full"),
        _entry(remaining=6, profile="dependencies"),
        _entry(remaining=5, profile="full"),
    ]

    trend = history.remediation_trend_with(_result(remaining=3, profile="full"))

    assert trend.direction == "improving"
    assert trend.samples == 3
    assert trend.remaining_actions_delta == -5
