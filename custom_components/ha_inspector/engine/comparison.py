"""Inspection comparison models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from .models import Finding
from .score import HealthStatus
if TYPE_CHECKING:
    from .result import InspectionResult


@dataclass(frozen=True, slots=True)
class InspectionComparison:
    """Compare two inspection results."""

    previous: InspectionResult
    current: InspectionResult

    @property
    def score_delta(self) -> int:
        """Return the score difference between both inspections."""
        return self.current.score - self.previous.score

    @property
    def health_delta(self) -> int:
        """Return the health score difference between both inspections."""
        return (
            self.current.health.score
            - self.previous.health.score
        )

    @property
    def findings(self) -> FindingsComparison:
        """Return the comparison of inspection findings."""
        previous = {
            finding.finding_id: finding
            for finding in self.previous.findings
        }
        current = {
            finding.finding_id: finding
            for finding in self.current.findings
        }

        added = tuple(
            current[finding_id]
            for finding_id in sorted(current.keys() - previous.keys())
        )

        removed = tuple(
            previous[finding_id]
            for finding_id in sorted(previous.keys() - current.keys())
        )

        unchanged = tuple(
            current[finding_id]
            for finding_id in sorted(current.keys() & previous.keys())
        )

        return FindingsComparison(
            added=added,
            removed=removed,
            unchanged=unchanged,
        )
    @property
    def categories(self) -> dict[str, CategoryComparison]:
        """Return the comparison grouped by category."""
        previous = self.previous.analytics.categories
        current = self.current.analytics.categories

        category_names = sorted(
            set(previous) | set(current)
        )

        result: dict[str, CategoryComparison] = {}

        for name in category_names:
            previous_health = previous.get(
                name,
                {
                    "health": {
                        "score": 100,
                        "status": HealthStatus.EXCELLENT.value,
                    }
                },
            )["health"]

            current_health = current.get(
                name,
                {
                    "health": {
                        "score": 100,
                        "status": HealthStatus.EXCELLENT.value,
                    }
                },
            )["health"]

            result[name] = CategoryComparison(
                previous_score=previous_health["score"],
                current_score=current_health["score"],
                previous_status=HealthStatus(
                    previous_health["status"]
                ),
                current_status=HealthStatus(
                    current_health["status"]
                ),
            )

        return result

@dataclass(frozen=True, slots=True)
class CategoryComparison:
    """Comparison of one inspection category."""

    previous_score: int
    current_score: int
    previous_status: HealthStatus
    current_status: HealthStatus

    @property
    def score_delta(self) -> int:
        """Return the score difference."""
        return self.current_score - self.previous_score

    @property
    def improved(self) -> bool:
        """Return whether the category improved."""
        return self.score_delta > 0

    @property
    def worsened(self) -> bool:
        """Return whether the category worsened."""
        return self.score_delta < 0

    @property
    def unchanged(self) -> bool:
        """Return whether the category stayed unchanged."""
        return self.score_delta == 0

@dataclass(frozen=True, slots=True)
class FindingsComparison:
    """Comparison of inspection findings."""

    added: tuple[Finding, ...]
    removed: tuple[Finding, ...]
    unchanged: tuple[Finding, ...]