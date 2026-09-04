"""Tests for remediation lifecycle summaries."""

from custom_components.ha_inspector.engine.historical_comparison import (
    HistoricalRemediationComparison,
)
from custom_components.ha_inspector.engine.remediation_lifecycle import (
    remediation_lifecycle_summary,
)


def _comparison(
    *,
    resolved_delta: int | None = 0,
    completed_actions_delta: int | None = 0,
    new_references_delta: int | None = 0,
    pending_delta: int | None = 0,
) -> HistoricalRemediationComparison:
    return HistoricalRemediationComparison(
        previous_tracked_entities=2,
        current_tracked_entities=2,
        tracked_entities_delta=0,
        previous_pending=1,
        current_pending=1,
        pending_delta=pending_delta,
        previous_in_progress=1,
        current_in_progress=1,
        in_progress_delta=0,
        previous_resolved=0,
        current_resolved=0,
        resolved_delta=resolved_delta,
        previous_completed_actions=0,
        current_completed_actions=0,
        completed_actions_delta=completed_actions_delta,
        previous_remaining_actions=2,
        current_remaining_actions=2,
        remaining_actions_delta=0,
        previous_new_references=0,
        current_new_references=0,
        new_references_delta=new_references_delta,
    )


def test_lifecycle_summary_is_idle_without_tracked_entities() -> None:
    summary = remediation_lifecycle_summary(
        {
            "tracked_entities": 0,
            "pending": 0,
            "in_progress": 0,
            "resolved": 0,
            "total_actions": 0,
            "completed_actions": 0,
            "remaining_actions": 0,
            "new_references": 0,
            "entities": [],
        },
        None,
    )

    assert summary["status"] == "idle"
    assert summary["resolved_since_previous"] == 0
    assert summary["newly_pending_since_previous"] == 0
    assert summary["new_references_delta"] == 0


def test_lifecycle_summary_reports_progress() -> None:
    summary = remediation_lifecycle_summary(
        {
            "tracked_entities": 2,
            "pending": 1,
            "in_progress": 1,
            "resolved": 0,
            "total_actions": 3,
            "completed_actions": 1,
            "remaining_actions": 2,
            "new_references": 0,
            "entities": [],
        },
        _comparison(completed_actions_delta=1),
    )

    assert summary["status"] == "progressing"


def test_lifecycle_summary_reports_resolution() -> None:
    summary = remediation_lifecycle_summary(
        {
            "tracked_entities": 2,
            "pending": 0,
            "in_progress": 0,
            "resolved": 2,
            "total_actions": 2,
            "completed_actions": 2,
            "remaining_actions": 0,
            "new_references": 0,
            "entities": [],
        },
        _comparison(resolved_delta=2, completed_actions_delta=2),
    )

    assert summary["status"] == "resolved"
    assert summary["resolved_since_previous"] == 2


def test_lifecycle_summary_reports_regression() -> None:
    summary = remediation_lifecycle_summary(
        {
            "tracked_entities": 2,
            "pending": 1,
            "in_progress": 1,
            "resolved": 0,
            "total_actions": 3,
            "completed_actions": 1,
            "remaining_actions": 2,
            "new_references": 1,
            "entities": [],
        },
        _comparison(new_references_delta=1),
    )

    assert summary["status"] == "regressed"
    assert summary["new_references_delta"] == 1


def test_lifecycle_summary_reports_active_work() -> None:
    summary = remediation_lifecycle_summary(
        {
            "tracked_entities": 2,
            "pending": 1,
            "in_progress": 1,
            "resolved": 0,
            "total_actions": 2,
            "completed_actions": 0,
            "remaining_actions": 2,
            "new_references": 0,
            "entities": [],
        },
        _comparison(),
    )

    assert summary["status"] == "active"


def test_lifecycle_summary_counts_new_pending_items() -> None:
    summary = remediation_lifecycle_summary(
        {
            "tracked_entities": 3,
            "pending": 2,
            "in_progress": 1,
            "resolved": 0,
            "total_actions": 3,
            "completed_actions": 0,
            "remaining_actions": 3,
            "new_references": 0,
            "entities": [],
        },
        _comparison(pending_delta=1),
    )

    assert summary["newly_pending_since_previous"] == 1
