"""Base class for HA Inspector rules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..context import InspectionContext
from ..models import Finding
from ..severity import Severity


@dataclass(frozen=True, slots=True)
class CompatibilityRuleDescriptor:
    """Metadata generated for rules not migrated to descriptors yet."""

    rule_id: str
    title: str
    category: str
    severity: Severity
    tags: tuple[str, ...] = field(default_factory=tuple)
    weight: int = 0
    recommendation: str | None = None

    @property
    def id(self) -> str:
        """Compatibility alias for the rule identifier."""
        return self.rule_id

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable descriptor."""
        severity = self.severity
        severity_value = (
            severity.label
            if hasattr(severity, "label")
            else getattr(severity, "value", str(severity))
        )
        return {
            "id": self.rule_id,
            "rule_id": self.rule_id,
            "title": self.title,
            "category": self.category,
            "severity": severity_value,
            "tags": list(self.tags),
            "weight": self.weight,
            "recommendation": self.recommendation,
        }


class BaseRule(ABC):
    """Base class for inspection rules."""

    rule_id: str

    @property
    def metadata(self) -> Any:
        """Return native, catalogued or synthesized rule metadata."""
        descriptor = getattr(self, "descriptor", None)
        if descriptor is not None:
            return descriptor

        rule_id = getattr(
            self,
            "rule_id",
            self.__class__.__name__,
        )

        # Import lazily to avoid coupling the base module to the
        # built-in rule catalog during initial package loading.
        from .catalog import RULE_DESCRIPTORS

        catalog_descriptor = RULE_DESCRIPTORS.get(rule_id)
        if catalog_descriptor is not None:
            return catalog_descriptor

        title = getattr(
            self,
            "title",
            self.__class__.__name__.removesuffix("Rule"),
        )
        category = getattr(
            self,
            "category",
            rule_id.split(".", 1)[0] if "." in rule_id else "general",
        )
        severity = getattr(self, "severity", Severity.INFO)
        tags = tuple(getattr(self, "tags", ()))
        weight = int(getattr(self, "weight", 0))
        recommendation = getattr(self, "recommendation", None)

        return CompatibilityRuleDescriptor(
            rule_id=rule_id,
            title=title,
            category=category,
            severity=severity,
            tags=tags,
            weight=weight,
            recommendation=recommendation,
        )

    @abstractmethod
    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        """Evaluate the context and return inspection findings."""
