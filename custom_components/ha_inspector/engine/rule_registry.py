"""Read-only rule metadata registry for HA Inspector."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from typing import Any

from .rules.base import BaseRule


class RuleRegistryError(RuntimeError):
    """Raised when a rule metadata registry cannot be built safely."""


@dataclass(frozen=True, slots=True)
class RuleRegistryEntry:
    """Immutable, JSON-friendly snapshot of one rule descriptor."""

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
        raw = rule.metadata.as_dict()

        rule_id = raw.get("rule_id", raw.get("id"))
        if not isinstance(rule_id, str) or not rule_id.strip():
            raise RuleRegistryError(
                f"{rule.__class__.__name__} has invalid rule metadata"
            )

        title = raw.get("title", rule_id)
        category = raw.get("category", "general")
        severity = raw.get("severity", "info")
        tags = raw.get("tags", ())
        weight = raw.get("weight", 0)
        recommendation = raw.get("recommendation")

        if not isinstance(title, str) or not title.strip():
            raise RuleRegistryError(
                f"Rule {rule_id!r} has an invalid title"
            )
        if not isinstance(category, str) or not category.strip():
            raise RuleRegistryError(
                f"Rule {rule_id!r} has an invalid category"
            )
        if not isinstance(severity, str) or not severity.strip():
            raise RuleRegistryError(
                f"Rule {rule_id!r} has an invalid severity"
            )
        if not isinstance(tags, (list, tuple)):
            raise RuleRegistryError(
                f"Rule {rule_id!r} has invalid tags"
            )

        normalized_tags = tuple(
            cls._normalize_tag(rule_id, tag)
            for tag in tags
        )

        return cls(
            rule_id=rule_id.strip(),
            title=title.strip(),
            category=category.strip(),
            severity=severity.strip(),
            tags=normalized_tags,
            weight=int(weight),
            recommendation=recommendation,
        )

    @staticmethod
    def _normalize_tag(rule_id: str, tag: Any) -> str:
        """Validate and normalize one tag."""
        if not isinstance(tag, str) or not tag.strip():
            raise RuleRegistryError(
                f"Rule {rule_id!r} contains an invalid tag"
            )
        return tag.strip()

    @property
    def id(self) -> str:
        """Compatibility alias for the rule identifier."""
        return self.rule_id

    def as_dict(self) -> dict[str, Any]:
        """Return a fresh JSON-serializable representation."""
        return {
            "id": self.rule_id,
            "rule_id": self.rule_id,
            "title": self.title,
            "category": self.category,
            "severity": self.severity,
            "tags": list(self.tags),
            "weight": self.weight,
            "recommendation": self.recommendation,
        }


class RuleRegistry:
    """Immutable catalogue of rule metadata."""

    def __init__(self, rules: Sequence[BaseRule]) -> None:
        entries: dict[str, RuleRegistryEntry] = {}

        for rule in rules:
            entry = RuleRegistryEntry.from_rule(rule)
            if entry.rule_id in entries:
                raise RuleRegistryError(
                    f"Duplicate rule identifier {entry.rule_id!r}"
                )
            entries[entry.rule_id] = entry

        self._entries = entries
        self._ordered_entries = tuple(
            entries[rule_id]
            for rule_id in sorted(entries)
        )

    def __len__(self) -> int:
        """Return the number of registered rules."""
        return len(self._ordered_entries)

    def __iter__(self) -> Iterator[RuleRegistryEntry]:
        """Iterate through entries in deterministic identifier order."""
        return iter(self._ordered_entries)

    def __contains__(self, rule_id: object) -> bool:
        """Return whether an identifier is registered."""
        return rule_id in self._entries

    @property
    def rule_ids(self) -> tuple[str, ...]:
        """Return registered identifiers in deterministic order."""
        return tuple(entry.rule_id for entry in self._ordered_entries)

    def list_rules(
        self,
        *,
        category: str | None = None,
        tag: str | None = None,
    ) -> tuple[RuleRegistryEntry, ...]:
        """List entries, optionally filtered by category and tag."""
        return tuple(
            entry
            for entry in self._ordered_entries
            if self._matches(entry, category=category, tag=tag)
        )

    def get_rule(self, rule_id: str) -> RuleRegistryEntry:
        """Return one entry or raise KeyError for an unknown identifier."""
        try:
            return self._entries[rule_id]
        except KeyError:
            raise KeyError(f"Unknown rule identifier: {rule_id}") from None

    def categories(self) -> tuple[str, ...]:
        """Return known categories in deterministic order."""
        return tuple(
            sorted({entry.category for entry in self._ordered_entries})
        )

    def tags(self) -> tuple[str, ...]:
        """Return known tags in deterministic order."""
        return tuple(
            sorted(
                {
                    tag
                    for entry in self._ordered_entries
                    for tag in entry.tags
                }
            )
        )

    def as_dicts(
        self,
        *,
        category: str | None = None,
        tag: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return fresh JSON-friendly dictionaries for external consumers."""
        return [
            entry.as_dict()
            for entry in self.list_rules(category=category, tag=tag)
        ]

    @staticmethod
    def _matches(
        entry: RuleRegistryEntry,
        *,
        category: str | None,
        tag: str | None,
    ) -> bool:
        """Return whether an entry satisfies all supplied filters."""
        if category is not None and entry.category != category:
            return False
        if tag is not None and tag not in entry.tags:
            return False
        return True


__all__ = [
    "RuleRegistry",
    "RuleRegistryEntry",
    "RuleRegistryError",
]
