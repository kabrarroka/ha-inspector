"""Dependency impact scoring and prioritization helpers."""

from __future__ import annotations

UNKNOWN_BASE_SCORE = 10
UNAVAILABLE_BASE_SCORE = 20
REFERENCE_WEIGHT = 5
MAX_REFERENCE_COUNT = 10


def dependency_impact_score(
    *,
    state: str,
    reference_count: int,
) -> int:
    """Return the diagnostic impact score for one dependency."""
    if state == "unknown":
        base_score = UNKNOWN_BASE_SCORE
    elif state == "unavailable":
        base_score = UNAVAILABLE_BASE_SCORE
    else:
        return 0

    normalized_reference_count = max(
        0,
        min(reference_count, MAX_REFERENCE_COUNT),
    )

    return base_score + normalized_reference_count * REFERENCE_WEIGHT


def dependency_priority(impact_score: int) -> str:
    """Return the priority label for one dependency impact score."""
    if impact_score >= 50:
        return "critical"
    if impact_score >= 35:
        return "high"
    if impact_score >= 20:
        return "medium"
    return "low"
