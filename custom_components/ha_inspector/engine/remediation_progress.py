"""Cross-inspection remediation progress helpers for HA Inspector."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import TypedDict

from .remediation_plans import (
    RemediationPlan,
    RemediationProgress,
    track_remediation_progress,
)


@dataclass(frozen=True, slots=True)
class RemediationProgressResult:
    """Contain remediation progress and plans requiring a new baseline."""

    progress: tuple[RemediationProgress, ...]
    new_baselines: tuple[RemediationPlan, ...]


class RemediationProgressEntityDiagnostics(TypedDict):
    """Compact remediation progress diagnostics for one entity."""

    entity_id: str
    status: str
    total_action_count: int
    completed_action_count: int
    remaining_action_count: int
    new_reference_count: int


class ResolvedRemediationItem(TypedDict):
    """Represent one resolved remediation item."""

    entity_id: str
    completed_action_count: int


class RemediationProgressDiagnostics(TypedDict):
    """Compact remediation progress diagnostics."""

    tracked_entities: int
    pending: int
    in_progress: int
    resolved: int
    total_actions: int
    completed_actions: int
    remaining_actions: int
    new_references: int
    entities: list[RemediationProgressEntityDiagnostics]


def empty_remediation_progress_diagnostics() -> RemediationProgressDiagnostics:
    """Return an empty remediation progress summary."""
    return {
        "tracked_entities": 0,
        "pending": 0,
        "in_progress": 0,
        "resolved": 0,
        "total_actions": 0,
        "completed_actions": 0,
        "remaining_actions": 0,
        "new_references": 0,
        "entities": [],
    }


def remediation_progress_diagnostics(
    progress: Iterable[RemediationProgress],
) -> RemediationProgressDiagnostics:
    """Build compact diagnostics from remediation progress."""
    items = sorted(progress, key=lambda item: item.entity_id)

    if not items:
        return empty_remediation_progress_diagnostics()

    entities: list[RemediationProgressEntityDiagnostics] = [
        {
            "entity_id": item.entity_id,
            "status": item.status,
            "total_action_count": item.total_action_count,
            "completed_action_count": item.completed_action_count,
            "remaining_action_count": item.remaining_action_count,
            "new_reference_count": item.new_reference_count,
        }
        for item in items
    ]

    return {
        "tracked_entities": len(items),
        "pending": sum(item.status == "pending" for item in items),
        "in_progress": sum(item.status == "in_progress" for item in items),
        "resolved": sum(item.status == "resolved" for item in items),
        "total_actions": sum(item.total_action_count for item in items),
        "completed_actions": sum(
            item.completed_action_count
            for item in items
        ),
        "remaining_actions": sum(
            item.remaining_action_count
            for item in items
        ),
        "new_references": sum(
            item.new_reference_count
            for item in items
        ),
        "entities": entities,
    }


def resolved_remediation_items(
    progress: Iterable[RemediationProgress],
) -> tuple[ResolvedRemediationItem, ...]:
    """Return resolved remediation items in stable entity-id order."""
    return tuple(
        {
            "entity_id": item.entity_id,
            "completed_action_count": item.completed_action_count,
        }
        for item in sorted(progress, key=lambda item: item.entity_id)
        if item.status == "resolved"
    )


def build_remediation_progress(
    baselines: Mapping[str, RemediationPlan],
    current_plans: Iterable[RemediationPlan],
) -> RemediationProgressResult:
    """Compare persisted baselines with current remediation plans."""
    current_by_entity = {
        plan.entity_id: plan
        for plan in current_plans
    }

    progress = tuple(
        track_remediation_progress(
            baselines[entity_id],
            current_by_entity.get(entity_id),
        )
        for entity_id in sorted(baselines)
    )

    new_baselines = tuple(
        current_by_entity[entity_id]
        for entity_id in sorted(current_by_entity)
        if entity_id not in baselines
    )

    return RemediationProgressResult(
        progress=progress,
        new_baselines=new_baselines,
    )


__all__ = [
    "RemediationProgressDiagnostics",
    "RemediationProgressEntityDiagnostics",
    "RemediationProgressResult",
    "ResolvedRemediationItem",
    "build_remediation_progress",
    "empty_remediation_progress_diagnostics",
    "remediation_progress_diagnostics",
    "resolved_remediation_items",
]
