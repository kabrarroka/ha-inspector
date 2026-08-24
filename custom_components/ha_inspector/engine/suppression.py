"""Finding suppression policy for HA Inspector."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from .models import Finding


def _normalize(values: Iterable[str] | None) -> frozenset[str]:
    """Normalize finding identifiers into an immutable set."""
    if values is None:
        return frozenset()

    if isinstance(values, str):
        values = (values,)

    return frozenset(
        value.strip()
        for value in values
        if isinstance(value, str) and value.strip()
    )


@dataclass(frozen=True, slots=True)
class FindingSuppressionPolicy:
    """Describe findings that should not affect an inspection result."""

    finding_ids: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        """Normalize configured finding identifiers."""
        object.__setattr__(
            self,
            "finding_ids",
            _normalize(self.finding_ids),
        )

    def is_suppressed(self, finding: Finding) -> bool:
        """Return whether a finding is suppressed."""
        return finding.finding_id in self.finding_ids

    def partition(
        self,
        findings: Iterable[Finding],
    ) -> tuple[list[Finding], list[Finding]]:
        """Split findings into active and suppressed collections."""
        active: list[Finding] = []
        suppressed: list[Finding] = []

        for finding in findings:
            target = suppressed if self.is_suppressed(finding) else active
            target.append(finding)

        return active, suppressed


__all__ = ["FindingSuppressionPolicy"]
