"""Inspection result model for HA Inspector."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Iterable

from .models import Finding
from .severity import Severity

from .health_score import HealthScore

RESULT_SCHEMA_VERSION = 2



@dataclass(slots=True)
class InspectionResult:
    """Contain the complete result of an HA Inspector execution."""

    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    findings: list[Finding] = field(default_factory=list)
    checks_executed: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    category_checks: dict[str, int] = field(default_factory=dict)
    category_findings: dict[str, int] = field(default_factory=dict)
    category_penalties: dict[str, float] = field(default_factory=dict)

    def add_many(self, findings: Iterable[Finding]) -> None:
        """Add multiple findings to the result."""
        self.findings.extend(findings)

    def record_rule(
        self,
        *,
        category: str,
        weight: int,
        findings: Iterable[Finding],
    ) -> None:
        """Record one executed rule and its scoring impact."""
        findings_list = list(findings)
        self.checks_executed += 1
        self.category_checks[category] = self.category_checks.get(category, 0) + 1
        self.category_findings[category] = (
            self.category_findings.get(category, 0) + len(findings_list)
        )
        penalty = HealthScore.calculate_penalty(
            weight=weight,
            severities=[
                finding.severity
                for finding in findings_list
            ],
        )
        self.category_penalties[category] = (
            self.category_penalties.get(category, 0.0) + penalty
        )
        self.add_many(findings_list)

    def finish(self) -> None:
        """Mark the inspection as finished."""
        self.finished_at = datetime.now(UTC)

    def count_by_severity(self, severity: Severity) -> int:
        """Return the number of findings for a severity."""
        return sum(finding.severity == severity for finding in self.findings)

    @property
    def total_findings(self) -> int:
        """Return the total number of findings."""
        return len(self.findings)

    @property
    def duration_seconds(self) -> float | None:
        """Return inspection duration in seconds."""
        if self.finished_at is None:
            return None
        return (self.finished_at - self.started_at).total_seconds()

    @property
    def score(self) -> int:
        """Calculate the weighted overall health score."""
        return HealthScore.calculate(self.category_penalties)

    @property
    def categories(self) -> dict[str, dict[str, int]]:
        """Return scoring information grouped by category."""
        return {
            category: {
                "score": HealthScore.calculate_category(
                    self.category_penalties.get(category, 0.0)
                ),
                "checks": self.category_checks.get(category, 0),
                "findings": self.category_findings.get(category, 0),
            }
            for category in sorted(self.category_checks)
        }

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the result."""
        return {
            "schema_version": RESULT_SCHEMA_VERSION,
            "started_at": self.started_at.isoformat(),
            "finished_at": (
                self.finished_at.isoformat()
                if self.finished_at is not None
                else None
            ),
            "duration_seconds": self.duration_seconds,
            "checks_executed": self.checks_executed,
            "total_findings": self.total_findings,
            "score": self.score,
            "categories": self.categories,
            "summary": {
                severity.label: self.count_by_severity(severity)
                for severity in Severity
            },
            "findings": [finding.as_dict() for finding in self.findings],
            "metadata": self.metadata,
        }
