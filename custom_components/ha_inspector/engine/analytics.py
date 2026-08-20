"""Inspection analytics for HA Inspector."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .score import HealthScore, HealthStatus, ScoreCalculator

if TYPE_CHECKING:
    from .result import InspectionResult


@dataclass(slots=True)
class InspectionAnalytics:
    """Provide derived metrics for an inspection result."""

    result: InspectionResult

    @property
    def health(self) -> HealthScore:
        """Return the complete weighted health score."""
        return ScoreCalculator.calculate_entries(
            self.result.scoring_entries
        )

    @property
    def score(self) -> int:
        """Return the weighted overall health score."""
        return self.health.score


    @property
    def health_status(self) -> HealthStatus:
        """Return the qualitative health status."""
        return self.health.status

    @property
    def categories(self) -> dict[str, dict[str, Any]]:
        """Return health information grouped by category."""
        return {
            category: {
                "health": ScoreCalculator.calculate_entries(
                    entry
                    for entry in self.result.scoring_entries
                    if entry.category == category
                ).as_dict(),
                "checks": self.result.category_checks.get(category, 0),
                "findings": self.result.category_findings.get(category, 0),
            }
            for category in sorted(self.result.category_checks)
        }


    @property
    def domain_health(self) -> dict[str, dict[str, Any]]:
        """Return user-facing health summaries for primary domains."""
        domains = (
            "storage",
            "system",
            "integrations",
            "entities",
        )

        categories = self.categories

        return {
            domain: (
                {
                    "domain": domain,
                    "status": "checked",
                    "health": categories[domain]["health"],
                    "checks": categories[domain]["checks"],
                    "findings": categories[domain]["findings"],
                }
                if domain in categories
                else {
                    "domain": domain,
                    "status": "not_checked",
                    "health": None,
                    "checks": 0,
                    "findings": 0,
                }
            )
            for domain in domains
        }

    @property
    def health_summary(self) -> dict[str, int]:
        """Return the number of categories grouped by health status."""
        summary = {
            status.value: 0
            for status in HealthStatus
        }

        for category in self.categories.values():
            summary[category["health"]["status"]] += 1

        return summary