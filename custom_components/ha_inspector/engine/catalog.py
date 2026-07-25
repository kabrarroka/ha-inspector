"""Serializable rule catalog for HA Inspector."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .rules.base import BaseRule


class RuleCatalog:
    """Build a deterministic, serializable catalog of inspection rules."""

    def __init__(self, rules: Iterable[BaseRule]) -> None:
        self._rules = list(rules)

    def as_list(self) -> list[dict[str, Any]]:
        """Return rule descriptors sorted by identifier."""
        entries = [rule.metadata.as_dict() for rule in self._rules]
        return sorted(entries, key=lambda entry: str(entry["id"]))

    def as_dict(self) -> dict[str, Any]:
        """Return the complete catalog payload."""
        rules = self.as_list()
        categories = sorted({str(rule["category"]) for rule in rules})
        return {
            "rules": rules,
            "total_rules": len(rules),
            "categories": categories,
        }
