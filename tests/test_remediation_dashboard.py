"""Tests for dashboard-oriented remediation summaries."""

from __future__ import annotations

from custom_components.ha_inspector.engine.remediation_dashboard import (
    remediation_dashboard_summary,
)
from custom_components.ha_inspector.engine.remediation_entity_summary import (
    RemediationEntitySummary,
)
from custom_components.ha_inspector.engine.remediation_lifecycle import (
    RemediationLifecycleSummary,
    empty_remediation_lifecycle_summary,
)
from custom_components.ha_inspector.engine.remediation_trends import (
    RemediationLifecycleTrend,
    remediation_lifecycle_trend,
)


def make_lifecycle(
    **changes: int | str,
) -> RemediationLifecycleSummary:
    """Build lifecycle diagnostics with optional overrides."""
    summary = empty_remediation_lifecycle_summary()
    summary.update(changes)
    return summary


def make_entity(
    entity_id: str,
    status: str = "pending",
    *,
    age_seconds: float | None = None,
    stalled: bool = False,
    urgency: str = "low",
) -> RemediationEntitySummary:
    """Build a remediation entity summary."""
    return {
        "entity_id": entity_id,
        "status": status,
        "age_seconds": age_seconds,
        "stalled": stalled,
        "urgency": urgency,
        "total_action_count": 1,
        "completed_action_count": 0,
        "remaining_action_count": 1,
        "new_reference_count": 0,
    }


def make_trend() -> RemediationLifecycleTrend:
    """Build an empty remediation trend."""
    return remediation_lifecycle_trend([])


def test_empty_dashboard_summary() -> None:
    """Empty remediation data produces an idle dashboard."""
    summary = remediation_dashboard_summary(
        make_lifecycle(),
        (),
        make_trend(),
    )

    assert summary == {
        "status": "idle",
        "tracked_entities": 0,
        "pending": 0,
        "in_progress": 0,
        "resolved": 0,
        "completed_actions": 0,
        "remaining_actions": 0,
        "new_references": 0,
        "stalled_entities": 0,
        "high_urgency_entities": 0,
        "oldest_active_age_seconds": None,
        "trend": "insufficient_data",
        "regression_count": 0,
        "remaining_actions_regression_count": 0,
        "new_references_regression_count": 0,
    }


def test_dashboard_preserves_lifecycle_counters() -> None:
    """Dashboard counters match the lifecycle summary."""
    lifecycle = make_lifecycle(
        status="progressing",
        tracked_entities=5,
        pending=2,
        in_progress=2,
        resolved=1,
        completed_actions=8,
        remaining_actions=4,
        new_references=3,
    )

    summary = remediation_dashboard_summary(
        lifecycle,
        (),
        make_trend(),
    )

    assert summary["status"] == "progressing"
    assert summary["tracked_entities"] == 5
    assert summary["pending"] == 2
    assert summary["in_progress"] == 2
    assert summary["resolved"] == 1
    assert summary["completed_actions"] == 8
    assert summary["remaining_actions"] == 4
    assert summary["new_references"] == 3


def test_dashboard_counts_only_active_stalled_entities() -> None:
    """Resolved entities do not contribute to stalled counts."""
    entities = (
        make_entity("sensor.a", stalled=True),
        make_entity("sensor.b", "in_progress", stalled=True),
        make_entity("sensor.c", "resolved", stalled=True),
        make_entity("sensor.d"),
    )

    summary = remediation_dashboard_summary(
        make_lifecycle(),
        entities,
        make_trend(),
    )

    assert summary["stalled_entities"] == 2


def test_dashboard_counts_only_active_high_urgency() -> None:
    """Only active high-urgency entities contribute."""
    entities = (
        make_entity("sensor.a", urgency="high"),
        make_entity("sensor.b", "in_progress", urgency="high"),
        make_entity("sensor.c", "resolved", urgency="high"),
        make_entity("sensor.d", urgency="medium"),
    )

    summary = remediation_dashboard_summary(
        make_lifecycle(),
        entities,
        make_trend(),
    )

    assert summary["high_urgency_entities"] == 2


def test_dashboard_reports_oldest_active_age() -> None:
    """The oldest known active remediation age is selected."""
    entities = (
        make_entity("sensor.a", age_seconds=100.0),
        make_entity("sensor.b", "in_progress", age_seconds=500.0),
        make_entity("sensor.c", "resolved", age_seconds=900.0),
        make_entity("sensor.d", age_seconds=None),
    )

    summary = remediation_dashboard_summary(
        make_lifecycle(),
        entities,
        make_trend(),
    )

    assert summary["oldest_active_age_seconds"] == 500.0


def test_dashboard_preserves_unknown_age() -> None:
    """Unknown active ages remain unknown."""
    entities = (
        make_entity("sensor.a"),
        make_entity("sensor.b", "in_progress"),
        make_entity("sensor.c", "resolved", age_seconds=1000.0),
    )

    summary = remediation_dashboard_summary(
        make_lifecycle(),
        entities,
        make_trend(),
    )

    assert summary["oldest_active_age_seconds"] is None


def test_dashboard_excludes_resolved_entities_from_age() -> None:
    """Resolved remediation ages never affect the active maximum."""
    entities = (make_entity("sensor.a", "resolved", age_seconds=1000.0),)

    summary = remediation_dashboard_summary(
        make_lifecycle(),
        entities,
        make_trend(),
    )

    assert summary["oldest_active_age_seconds"] is None


def test_dashboard_exposes_regression_counters() -> None:
    """Dashboard reuses the historical trend and regression counters."""
    entries = [
        {
            "inspection_scope": "scope-full",
            "remediation": {
                "pending": 2,
                "in_progress": 0,
                "resolved": 0,
                "completed_actions": 0,
                "remaining_actions": 4,
                "new_references": 0,
            },
        },
        {
            "inspection_scope": "scope-full",
            "remediation": {
                "pending": 2,
                "in_progress": 0,
                "resolved": 0,
                "completed_actions": 0,
                "remaining_actions": 5,
                "new_references": 1,
            },
        },
    ]

    trend = remediation_lifecycle_trend(entries)

    summary = remediation_dashboard_summary(
        make_lifecycle(),
        (),
        trend,
    )

    assert summary["trend"] == "declining"
    assert summary["regression_count"] == 1
    assert summary["remaining_actions_regression_count"] == 1
    assert summary["new_references_regression_count"] == 1


def test_dashboard_does_not_modify_inputs() -> None:
    """Building a dashboard summary leaves its inputs unchanged."""
    lifecycle = make_lifecycle()
    entities = (make_entity("sensor.a", age_seconds=100.0),)
    trend = make_trend()

    original_lifecycle = lifecycle.copy()
    original_entities = tuple(item.copy() for item in entities)

    remediation_dashboard_summary(
        lifecycle,
        entities,
        trend,
    )

    assert lifecycle == original_lifecycle
    assert entities == original_entities
