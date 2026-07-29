"""Health score calculation for HA Inspector."""

from __future__ import annotations

from enum import StrEnum
from typing import Mapping

from .severity import Severity

SEVERITY_WEIGHT: Mapping[Severity, float] = {
    Severity.INFO: 0.0,
    Severity.WARNING: 0.30,
    Severity.ERROR: 0.70,
    Severity.CRITICAL: 1.0,
}


class HealthStatus(StrEnum):
    """Represent the qualitative health status."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


def penalty_for_finding(*, weight: int, severity: Severity) -> float:
    """Calculate the penalty produced by one finding."""
    return max(0, weight) * SEVERITY_WEIGHT[severity]


def score_from_penalties(penalties: Mapping[str, float]) -> int:
    """Calculate the overall score from category penalties."""
    return max(0, 100 - round(sum(penalties.values())))


def category_score(penalty: float) -> int:
    """Calculate the score for one category."""
    return max(0, 100 - round(penalty))


def status_for_score(score: int) -> HealthStatus:
    """Return the qualitative status for a health score."""
    if score >= 90:
        return HealthStatus.EXCELLENT
    if score >= 75:
        return HealthStatus.GOOD
    if score >= 50:
        return HealthStatus.FAIR
    if score >= 25:
        return HealthStatus.POOR
    return HealthStatus.CRITICAL