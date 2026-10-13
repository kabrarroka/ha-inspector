"""Per-entity remediation summaries for HA Inspector."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import TypedDict

from .remediation_plans import RemediationProgress
from .remediation_stalled import (
    DEFAULT_STALLED_THRESHOLD_SECONDS,
    is_remediation_stalled,
)
from .remediation_urgency import (
    RemediationUrgency,
    classify_remediation_urgency,
)


class RemediationEntitySummary(TypedDict):
    """Summarize remediation age, status and progress for one entity."""

    entity_id: str
    status: str
    age_seconds: float | None
    stalled: bool
    urgency: RemediationUrgency
    total_action_count: int
    completed_action_count: int
    remaining_action_count: int
    new_reference_count: int


def remediation_entity_summaries(
    progress: Iterable[RemediationProgress],
    ages: Mapping[str, float | None],
    *,
    threshold_seconds: float = DEFAULT_STALLED_THRESHOLD_SECONDS,
) -> tuple[RemediationEntitySummary, ...]:
    """Build deterministic per-entity remediation summaries."""
    summaries: list[RemediationEntitySummary] = []

    for item in sorted(progress, key=lambda value: value.entity_id):
        age_seconds = ages.get(item.entity_id)

        stalled = is_remediation_stalled(
            item.status,
            age_seconds,
            threshold_seconds=threshold_seconds,
        )

        urgency = classify_remediation_urgency(
            item,
            age_seconds,
            threshold_seconds=threshold_seconds,
        )

        summaries.append(
            {
                "entity_id": item.entity_id,
                "status": item.status,
                "age_seconds": age_seconds,
                "stalled": stalled,
                "urgency": urgency,
                "total_action_count": item.total_action_count,
                "completed_action_count": item.completed_action_count,
                "remaining_action_count": item.remaining_action_count,
                "new_reference_count": item.new_reference_count,
            }
        )

    return tuple(summaries)


__all__ = [
    "RemediationEntitySummary",
    "remediation_entity_summaries",
]
