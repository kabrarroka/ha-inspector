"""Rule selection primitives for HA Inspector."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import TypeAlias

from .rules.base import BaseRule

RulePredicate: TypeAlias = Callable[[BaseRule], bool]


@dataclass(frozen=True, slots=True, init=False)
class RuleFilter:
    """Select rules using optional identifiers, categories and a predicate.

    Every configured criterion must match. Omitting every criterion selects all
    rules. Passing an explicit empty iterable selects no rules for that
    criterion.
    """

    rule_ids: frozenset[str] | None
    categories: frozenset[str] | None
    predicate: RulePredicate | None

    def __init__(
        self,
        *,
        rule_ids: Iterable[str] | None = None,
        categories: Iterable[str] | None = None,
        predicate: RulePredicate | None = None,
    ) -> None:
        normalized_rule_ids = self._normalize(rule_ids, "rule_ids")
        normalized_categories = self._normalize(
            categories,
            "categories",
        )

        object.__setattr__(self, "rule_ids", normalized_rule_ids)
        object.__setattr__(self, "categories", normalized_categories)
        object.__setattr__(self, "predicate", predicate)

    @staticmethod
    def _normalize(
        values: Iterable[str] | None,
        field_name: str,
    ) -> frozenset[str] | None:
        """Normalize and validate one textual criterion."""
        if values is None:
            return None

        normalized = frozenset(value.strip() for value in values)
        if any(not value for value in normalized):
            raise ValueError(f"{field_name} must not contain empty values")

        return normalized

    def matches(self, rule: BaseRule) -> bool:
        """Return whether a rule satisfies every configured criterion."""
        descriptor = rule.metadata

        if (
            self.rule_ids is not None
            and descriptor.rule_id not in self.rule_ids
        ):
            return False

        if (
            self.categories is not None
            and descriptor.category not in self.categories
        ):
            return False

        if self.predicate is not None and not self.predicate(rule):
            return False

        return True
