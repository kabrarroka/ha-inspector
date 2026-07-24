"""Typed descriptors used by HA Inspector rules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RuleDescriptor:
    """Describe one inspection rule independently of its implementation."""

    rule_id: str
    category: str
    title: str
    description: str
    weight: int
    tags: tuple[str, ...] = ()
    enabled: bool = True

    def __post_init__(self) -> None:
        """Validate descriptor values."""
        if not self.rule_id or "." not in self.rule_id:
            raise ValueError(
                "Rule IDs must use dotted notation, for example system.info"
            )
        if not self.category:
            raise ValueError("Rule category cannot be empty")
        if not 0 <= self.weight <= 100:
            raise ValueError("Rule weight must be between 0 and 100")

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""
        return {
            "id": self.rule_id,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "weight": self.weight,
            "tags": list(self.tags),
            "enabled": self.enabled,
        }
