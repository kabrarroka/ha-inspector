"""Tests for remediation trends based on effective inspection scope."""

from __future__ import annotations

from typing import Any

from custom_components.ha_inspector.engine.remediation_trends import (
    remediation_lifecycle_trend,
)


def _entry(
    remaining: int,
    *,
    scope: str | None,
    profile: str | None = None,
) -> dict[str, Any]:
    """Build a compact remediation history entry."""
    return {
        "profile": profile,
        "inspection_scope": scope,
        "remediation": {
            "pending": 1,
            "in_progress": 0,
            "resolved": 0,
            "completed_actions": 0,
            "remaining_actions": remaining,
            "new_references": 0,
        },
    }


def test_trend_supports_inspections_without_profile() -> None:
    """Inspections without explicit profiles can be compared."""
    trend = remediation_lifecycle_trend(
        [
            _entry(8, scope="scope-a"),
            _entry(5, scope="scope-a"),
        ]
    )

    assert trend.direction == "improving"
    assert trend.samples == 2
    assert trend.remaining_actions_delta == -3


def test_trend_compares_equivalent_scopes_across_profiles() -> None:
    """Equivalent effective configurations are comparable."""
    trend = remediation_lifecycle_trend(
        [
            _entry(8, scope="scope-a", profile="full"),
            _entry(4, scope="scope-a"),
        ]
    )

    assert trend.direction == "improving"
    assert trend.samples == 2
    assert trend.remaining_actions_delta == -4


def test_trend_excludes_different_scopes() -> None:
    """Different effective configurations must not be mixed."""
    trend = remediation_lifecycle_trend(
        [
            _entry(10, scope="scope-a"),
            _entry(8, scope="scope-b"),
            _entry(6, scope="scope-a"),
            _entry(3, scope="scope-b"),
        ]
    )

    assert trend.direction == "improving"
    assert trend.samples == 2
    assert trend.remaining_actions_delta == -5


def test_trend_does_not_mix_legacy_entries() -> None:
    """Legacy entries without a scope are not comparable."""
    trend = remediation_lifecycle_trend(
        [
            _entry(10, scope=None, profile="full"),
            _entry(6, scope="scope-a", profile="full"),
        ]
    )

    assert trend.direction == "insufficient_data"
    assert trend.samples == 1
    assert trend.remaining_actions_delta is None
