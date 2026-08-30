"""Dependency diagnostics for domain health and dashboard summaries."""

from __future__ import annotations

from typing import TypedDict

from .entities_state import DependencyHealthSummary, EntitiesState


class DependencyDiagnostics(TypedDict):
    """Compact dependency diagnostics exposed by inspection results."""

    affected_entities: int
    unavailable: int
    unknown: int
    critical: int
    high: int
    medium: int
    low: int
    max_impact_score: int


def empty_dependency_diagnostics() -> DependencyDiagnostics:
    """Return an empty dependency diagnostics summary."""
    return {
        "affected_entities": 0,
        "unavailable": 0,
        "unknown": 0,
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "max_impact_score": 0,
    }


def dependency_diagnostics(
    entities: EntitiesState,
) -> DependencyDiagnostics:
    """Build compact diagnostics for problematic entity dependencies."""
    dependencies: list[DependencyHealthSummary] = [
        *entities.unavailable_dependencies,
        *entities.unknown_dependencies,
    ]

    priority_counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    for dependency in dependencies:
        if dependency.priority in priority_counts:
            priority_counts[dependency.priority] += 1

    return {
        "affected_entities": len(dependencies),
        "unavailable": len(entities.unavailable_dependencies),
        "unknown": len(entities.unknown_dependencies),
        "critical": priority_counts["critical"],
        "high": priority_counts["high"],
        "medium": priority_counts["medium"],
        "low": priority_counts["low"],
        "max_impact_score": max(
            (
                dependency.impact_score
                for dependency in dependencies
            ),
            default=0,
        ),
    }
