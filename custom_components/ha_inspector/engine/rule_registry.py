"""Immutable metadata registry for HA Inspector rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .rules.base import BaseRule


class RuleRegistryError(ValueError):
    """Raised when the rule registry cannot be constructed."""


@dataclass(frozen=True, slots=True)
class RuleRegistryEntry:
    """Immutable metadata snapshot for a rule."""

    rule_id: str
    title: str
    category: str
    severity: str
    tags: tuple[str, ...]
    weight: int
    recommendation: str | None

    @classmethod
    def from_rule(cls, rule: BaseRule) -> "RuleRegistryEntry":
        """Create an entry without executing the rule."""
        metadata = rule.metadata
        data = metadata.as_dict()

        rule_id = str(
            getattr(rule, "rule_id", "")
            or data.get("rule_id")
            or data.get("id")
            or ""
        ).strip()

        if not rule_id:
            raise RuleRegistryError(
                "Rule metadata must define a rule_id"
            )

        severity = data.get(
            "severity",
            getattr(metadata, "severity", "info"),
        )

        severity_value = getattr(
            severity,
            "label",
            getattr(severity, "value", severity),
        )

        return cls(
            rule_id=rule_id,
            title=str(data.get("title", "")),
            category=str(data.get("category", "general")),
            severity=str(severity_value),
            tags=tuple(
                str(tag)
                for tag in data.get("tags", ())
            ),
            weight=int(data.get("weight", 0)),
            recommendation=data.get(
                "recommendation",
                getattr(metadata, "recommendation", None),
            ),
        )

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly copy of the entry."""
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "category": self.category,
            "severity": self.severity,
            "tags": list(self.tags),
            "weight": self.weight,
            "recommendation": self.recommendation,
        }


class RuleRegistry:
    """Catalog immutable metadata for a collection of rules."""

    def __init__(self, rules: Iterable[BaseRule]) -> None:
        entries: dict[str, RuleRegistryEntry] = {}

        for rule in rules:
            entry = RuleRegistryEntry.from_rule(rule)

            if entry.rule_id in entries:
                raise RuleRegistryError(
                    f"Duplicate rule identifier: {entry.rule_id}"
                )

            entries[entry.rule_id] = entry

        self._entries = dict(sorted(entries.items()))

    def __len__(self) -> int:
        """Return the number of registered rules."""
        return len(self._entries)

    def __contains__(self, rule_id: object) -> bool:
        """Return whether a rule identifier is registered."""
        return rule_id in self._entries

    def get_rule(self, rule_id: str) -> RuleRegistryEntry:
        """Return one registered rule entry."""
        return self._entries[rule_id]

    def list_rules(
        self,
        *,
        category: str | None = None,
        tag: str | None = None,
    ) -> tuple[RuleRegistryEntry, ...]:
        """Return entries filtered by category and tag."""
        entries: Iterable[RuleRegistryEntry] = self._entries.values()

        if category is not None:
            entries = (
                entry for entry in entries if entry.category == category
            )

        if tag is not None:
            entries = (
                entry for entry in entries if tag in entry.tags
            )

        return tuple(entries)

    def categories(self) -> tuple[str, ...]:
        """Return all known categories in deterministic order."""
        return tuple(
            sorted({entry.category for entry in self._entries.values()})
        )

    def tags(self) -> tuple[str, ...]:
        """Return all known tags in deterministic order."""
        return tuple(
            sorted(
                {
                    tag
                    for entry in self._entries.values()
                    for tag in entry.tags
                }
            )
        )

    def as_dicts(self) -> list[dict[str, Any]]:
        """Return JSON-friendly copies of all registry entries."""
        return [entry.as_dict() for entry in self._entries.values()]
