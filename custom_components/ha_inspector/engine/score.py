"""Health score calculation for HA Inspector."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from .severity import Severity

MAX_HEALTH_SCORE = 100

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


class ScoreFinding(Protocol):
    """Describe the minimum finding interface required for scoring."""

    @property
    def severity(self) -> Severity:
        """Return the finding severity."""

    @property
    def weight(self) -> int:
        """Return the finding weight."""

@dataclass(frozen=True, slots=True)
class ScoringEntry:
    """Represent one scoring contribution."""

    category: str
    weight: int
    severity: Severity

    @property
    def penalty(self) -> float:
        """Return the calculated penalty."""
        return penalty_for_finding(
            weight=self.weight,
            severity=self.severity,
        )

@dataclass(frozen=True, slots=True)
class HealthScore:
    """Represent the calculated health of an installation."""

    score: int
    max_score: int
    status: HealthStatus
    penalty: float

    def as_dict(self) -> dict[str, int | float | str]:
        """Return a serializable representation of the score."""
        return {
            "score": self.score,
            "max_score": self.max_score,
            "status": self.status.value,
            "penalty": self.penalty,
        }


def penalty_for_finding(*, weight: int, severity: Severity) -> float:
    """Calculate the penalty produced by one finding."""
    normalized_weight = max(0, weight)
    return normalized_weight * SEVERITY_WEIGHT[severity]


def score_from_penalties(penalties: Mapping[str, float]) -> int:
    """Calculate the overall score from category penalties."""
    total_penalty = sum(max(0.0, penalty) for penalty in penalties.values())
    return max(0, MAX_HEALTH_SCORE - round(total_penalty))


def category_score(penalty: float) -> int:
    """Calculate the score for one category."""
    return max(0, MAX_HEALTH_SCORE - round(max(0.0, penalty)))


def status_for_score(score: int) -> HealthStatus:
    """Return the qualitative status for a health score."""
    normalized_score = max(0, min(MAX_HEALTH_SCORE, score))

    if normalized_score >= 90:
        return HealthStatus.EXCELLENT
    if normalized_score >= 75:
        return HealthStatus.GOOD
    if normalized_score >= 50:
        return HealthStatus.FAIR
    if normalized_score >= 25:
        return HealthStatus.POOR
    return HealthStatus.CRITICAL


class ScoreCalculator:
    """Calculate health scores from rule findings."""

    @staticmethod
    def calculate_entries(
        entries: Iterable[ScoringEntry],
        *,
        max_score: int = MAX_HEALTH_SCORE,
    ) -> HealthScore:
        """Calculate the health score from scoring entries."""
        normalized_max_score = max(0, max_score)
        penalty = sum(entry.penalty for entry in entries)
        score = max(
            0,
            normalized_max_score - round(penalty),
        )

        return HealthScore(
            score=score,
            max_score=normalized_max_score,
            status=status_for_score(score),
            penalty=penalty,
        )

    @staticmethod
    def calculate(
        findings: Iterable[ScoreFinding],
        *,
        max_score: int = MAX_HEALTH_SCORE,
    ) -> HealthScore:
        """Calculate the health score for a collection of findings."""
        normalized_max_score = max(0, max_score)

        penalty = sum(
            penalty_for_finding(
                weight=finding.weight,
                severity=finding.severity,
            )
            for finding in findings
        )

        score = max(
            0,
            normalized_max_score - round(penalty),
        )

        return HealthScore(
            score=score,
            max_score=normalized_max_score,
            status=status_for_score(score),
            penalty=penalty,
        )