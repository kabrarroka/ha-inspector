"""Inspection result model for HA Inspector."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Iterable

from .models import Finding
from .severity import Severity


@dataclass(slots=True)
class InspectionResult:
    """Contain the complete result of an HA Inspector execution."""

    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    findings: list[Finding] = field(default_factory=list)
    checks_executed: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def add(self, finding: Finding) -> None:
        """Add one finding to the result."""
        self.findings.append(finding)

    def add_many(self, findings: Iterable[Finding]) -> None:
        """Add multiple findings to the result."""
        self.findings.extend(findings)

    def finish(self) -> None:
        """Mark the inspection as finished."""
        self.finished_at = datetime.now(UTC)

    def count_by_severity(self, severity: Severity) -> int:
        """Return the number of findings for a severity."""
        return sum(
            finding.severity == severity
            for finding in self.findings
        )

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
        """Calculate a provisional health score from 0 to 100."""
        penalty = sum(
            {
                Severity.INFO: 0,
                Severity.WARNING: 3,
                Severity.ERROR: 10,
                Severity.CRITICAL: 25,
            }[finding.severity]
            for finding in self.findings
        )

        return max(0, 100 - penalty)

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the result."""
        return {
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
            "summary": {
                severity.label: self.count_by_severity(severity)
                for severity in Severity
            },
            "findings": [
                finding.as_dict()
                for finding in self.findings
            ],
            "metadata": self.metadata,
        }