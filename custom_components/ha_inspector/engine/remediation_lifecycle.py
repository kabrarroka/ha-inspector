"""Remediation lifecycle summaries for HA Inspector."""

from __future__ import annotations

from typing import TypedDict

from .historical_comparison import HistoricalRemediationComparison
from .remediation_progress import RemediationProgressDiagnostics


class RemediationLifecycleSummary(TypedDict):
    """Summarize the current remediation lifecycle state."""

    status: str
    tracked_entities: int
    pending: int
    in_progress: int
    resolved: int
    completed_actions: int
    remaining_actions: int
    new_references: int
    resolved_since_previous: int
    newly_pending_since_previous: int
    new_references_delta: int


def empty_remediation_lifecycle_summary() -> RemediationLifecycleSummary:
    """Return an empty remediation lifecycle summary."""
    return {
        "status": "idle",
        "tracked_entities": 0,
        "pending": 0,
        "in_progress": 0,
        "resolved": 0,
        "completed_actions": 0,
        "remaining_actions": 0,
        "new_references": 0,
        "resolved_since_previous": 0,
        "newly_pending_since_previous": 0,
        "new_references_delta": 0,
    }


def remediation_lifecycle_summary(
    progress: RemediationProgressDiagnostics,
    comparison: HistoricalRemediationComparison | None,
) -> RemediationLifecycleSummary:
    """Build a compact remediation lifecycle summary."""
    resolved_since_previous = _positive_delta(
        comparison.resolved_delta
        if comparison is not None
        else None
    )
    newly_pending_since_previous = _positive_delta(
        comparison.pending_delta
        if comparison is not None
        else None
    )
    new_references_delta = (
        comparison.new_references_delta
        if (
            comparison is not None
            and comparison.new_references_delta is not None
        )
        else 0
    )

    status = _lifecycle_status(
        progress,
        comparison,
        new_references_delta,
    )

    return {
        "status": status,
        "tracked_entities": progress["tracked_entities"],
        "pending": progress["pending"],
        "in_progress": progress["in_progress"],
        "resolved": progress["resolved"],
        "completed_actions": progress["completed_actions"],
        "remaining_actions": progress["remaining_actions"],
        "new_references": progress["new_references"],
        "resolved_since_previous": resolved_since_previous,
        "newly_pending_since_previous": newly_pending_since_previous,
        "new_references_delta": new_references_delta,
    }


def _lifecycle_status(
    progress: RemediationProgressDiagnostics,
    comparison: HistoricalRemediationComparison | None,
    new_references_delta: int,
) -> str:
    """Return the qualitative remediation lifecycle status."""
    if progress["tracked_entities"] == 0:
        return "idle"

    if progress["remaining_actions"] == 0:
        return "resolved"

    if (
        progress["new_references"] > 0
        and new_references_delta > 0
    ):
        return "regressed"

    if comparison is not None and (
        _positive_delta(comparison.completed_actions_delta) > 0
        or _positive_delta(comparison.resolved_delta) > 0
    ):
        return "progressing"

    return "active"


def _positive_delta(value: int | None) -> int:
    """Return only positive lifecycle deltas."""
    if value is None or value <= 0:
        return 0
    return value


__all__ = [
    "RemediationLifecycleSummary",
    "empty_remediation_lifecycle_summary",
    "remediation_lifecycle_summary",
]
