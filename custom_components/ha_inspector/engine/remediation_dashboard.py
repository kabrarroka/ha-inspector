"""Dashboard-oriented remediation summaries for HA Inspector."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TypedDict

from .remediation_entity_summary import RemediationEntitySummary
from .remediation_lifecycle import RemediationLifecycleSummary
from .remediation_trends import RemediationLifecycleTrend
from .trends import TrendDirection

_ACTIVE_STATUSES = frozenset({"pending", "in_progress"})


class RemediationDashboardSummary(TypedDict):
    """Compact remediation information suitable for dashboards."""

    status: str
    tracked_entities: int
    pending: int
    in_progress: int
    resolved: int
    completed_actions: int
    remaining_actions: int
    new_references: int
    stalled_entities: int
    high_urgency_entities: int
    oldest_active_age_seconds: float | None
    trend: TrendDirection
    regression_count: int
    remaining_actions_regression_count: int
    new_references_regression_count: int


def remediation_dashboard_summary(
    lifecycle: RemediationLifecycleSummary,
    entities: Iterable[RemediationEntitySummary],
    trend: RemediationLifecycleTrend,
) -> RemediationDashboardSummary:
    """Build a dashboard summary from existing remediation diagnostics."""

    active_entities = [
        entity for entity in entities if entity["status"] in _ACTIVE_STATUSES
    ]

    stalled_entities = sum(entity["stalled"] for entity in active_entities)

    high_urgency_entities = sum(
        entity["urgency"] == "high" for entity in active_entities
    )

    active_ages = [
        age for entity in active_entities if (age := entity["age_seconds"]) is not None
    ]

    oldest_active_age_seconds = max(active_ages) if active_ages else None

    return {
        "status": lifecycle["status"],
        "tracked_entities": lifecycle["tracked_entities"],
        "pending": lifecycle["pending"],
        "in_progress": lifecycle["in_progress"],
        "resolved": lifecycle["resolved"],
        "completed_actions": lifecycle["completed_actions"],
        "remaining_actions": lifecycle["remaining_actions"],
        "new_references": lifecycle["new_references"],
        "stalled_entities": stalled_entities,
        "high_urgency_entities": high_urgency_entities,
        "oldest_active_age_seconds": oldest_active_age_seconds,
        "trend": trend.direction,
        "regression_count": trend.regression_count,
        "remaining_actions_regression_count": (
            trend.remaining_actions_regression_count
        ),
        "new_references_regression_count": (trend.new_references_regression_count),
    }


__all__ = [
    "RemediationDashboardSummary",
    "remediation_dashboard_summary",
]
