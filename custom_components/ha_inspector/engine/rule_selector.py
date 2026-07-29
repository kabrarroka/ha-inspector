"""Rule selection and immutable execution plans."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from .rule_registry import RuleRegistry, RuleRegistryEntry


@dataclass(frozen=True, slots=True)
class RuleExecutionPlan:
    """Immutable and deterministically ordered rule execution plan."""

    rule_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate and normalize the execution plan."""
        normalized = tuple(sorted(set(self.rule_ids)))
        object.__setattr__(self, "rule_ids", normalized)

    def __iter__(self) -> Iterator[str]:
        """Iterate over selected rule identifiers."""
        return iter(self.rule_ids)

    def __len__(self) -> int:
        """Return the number of selected rules."""
        return len(self.rule_ids)

    def __contains__(self, rule_id: object) -> bool:
        """Return whether a rule identifier is in the plan."""
        return rule_id in self.rule_ids

    def as_dict(self) -> dict[str, list[str]]:
        """Return a JSON-safe representation of the plan."""
        return {"rule_ids": list(self.rule_ids)}


class RuleSelector:
    """Select rule identifiers from a rule metadata registry."""

    def __init__(self, registry: RuleRegistry) -> None:
        """Initialize the selector."""
        self._registry = registry

    def select(
        self,
        *,
        include_rule_ids: Iterable[str] | None = None,
        include_categories: Iterable[str] | None = None,
        include_tags: Iterable[str] | None = None,
        exclude_rule_ids: Iterable[str] | None = None,
        exclude_categories: Iterable[str] | None = None,
        exclude_tags: Iterable[str] | None = None,
    ) -> RuleExecutionPlan:
        """Build an immutable rule execution plan.

        Inclusion filters are combined using AND between filter groups:

        - rule identifier
        - category
        - tag

        Multiple values inside the same group use OR semantics.

        Exclusion filters are then applied using OR semantics. A rule is
        excluded when it matches any exclusion criterion.

        When no inclusion filters are supplied, every registered rule is
        initially selected.
        """
        included_ids = self._normalize(include_rule_ids)
        included_categories = self._normalize(include_categories)
        included_tags = self._normalize(include_tags)

        excluded_ids = self._normalize(exclude_rule_ids)
        excluded_categories = self._normalize(exclude_categories)
        excluded_tags = self._normalize(exclude_tags)

        self._validate_rule_ids(included_ids)
        self._validate_rule_ids(excluded_ids)

        selected: list[str] = []

        for entry in self._registry.list_rules():
            if not self._matches_inclusion(
                entry,
                rule_ids=included_ids,
                categories=included_categories,
                tags=included_tags,
            ):
                continue

            if self._matches_exclusion(
                entry,
                rule_ids=excluded_ids,
                categories=excluded_categories,
                tags=excluded_tags,
            ):
                continue

            selected.append(entry.rule_id)

        return RuleExecutionPlan(tuple(selected))

    def _validate_rule_ids(self, rule_ids: frozenset[str]) -> None:
        """Raise KeyError when a requested rule identifier is unknown."""
        for rule_id in sorted(rule_ids):
            self._registry.get_rule(rule_id)

    @staticmethod
    def _matches_inclusion(
        entry: RuleRegistryEntry,
        *,
        rule_ids: frozenset[str],
        categories: frozenset[str],
        tags: frozenset[str],
    ) -> bool:
        """Return whether an entry satisfies all inclusion groups."""
        if rule_ids and entry.rule_id not in rule_ids:
            return False

        if categories and entry.category not in categories:
            return False

        if tags and not tags.intersection(entry.tags):
            return False

        return True

    @staticmethod
    def _matches_exclusion(
        entry: RuleRegistryEntry,
        *,
        rule_ids: frozenset[str],
        categories: frozenset[str],
        tags: frozenset[str],
    ) -> bool:
        """Return whether an entry matches any exclusion criterion."""
        if entry.rule_id in rule_ids:
            return True

        if entry.category in categories:
            return True

        if tags.intersection(entry.tags):
            return True

        return False

    @staticmethod
    def _normalize(values: Iterable[str] | None) -> frozenset[str]:
        """Normalize optional selection values."""
        if values is None:
            return frozenset()

        if isinstance(values, str):
            values = (values,)

        return frozenset(
            value.strip()
            for value in values
            if isinstance(value, str) and value.strip()
        )
