"""Result model for HA Inspector rules."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .category import Category
from .severity import Severity


@dataclass(slots=True)
class RuleResult:
    """Represent the result produced by an inspection rule."""

    rule_id: str
    category: Category
    severity: Severity
    summary: str
    details: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    documentation_url: str | None = None
    execution_time_ms: float | None = None

    @property
    def is_problem(self) -> bool:
        """Return whether the result represents a detected problem."""
        return self.severity in {
            Severity.WARNING,
            Severity.CRITICAL,
            Severity.ERROR,
        }

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the result."""
        result = asdict(self)

        result["category"] = self.category.value
        result["severity"] = self.severity.value

        return result
