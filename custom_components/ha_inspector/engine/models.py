"""Data models used by the HA Inspector engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .severity import Severity


@dataclass(frozen=True, slots=True)
class Finding:
    """Represent a single finding produced by an inspection rule."""

    finding_id: str
    severity: Severity
    title: str
    description: str
    recommendation: str | None = None
    documentation_url: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the finding."""
        return {
            "id": self.finding_id,
            "severity": self.severity.label,
            "title": self.title,
            "description": self.description,
            "recommendation": self.recommendation,
            "documentation_url": self.documentation_url,
            "data": self.data,
        }