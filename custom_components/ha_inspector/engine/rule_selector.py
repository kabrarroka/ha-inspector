"""High-level rule selection API for HA Inspector."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from .execution_plan import RuleExecutionPlan
from .rule_filter import RuleFilter
from .rule_registry import RuleRegistry
from .rules.base import BaseRule


class RuleSelectionError(ValueError):
    """Raised when a rule selection request is invalid."""


@dataclass(frozen=True, slots=True, init=False)
class RuleSelection:
    """Normalized immutable rule selection request."""

    include_rule_ids: frozenset[str] | None
    include_categories: frozenset[str] | None
    include_tags: frozenset[str] | None
    exclude_rule_ids: frozenset[str]
    exclude_categories: frozenset[str]
    exclude_tags: frozenset[str]

    def __init__(
        self,
        *,
        include_rule_ids: Iterable[str] | None = None,
        include_categories: Iterable[str] | None = None,
        include_tags: Iterable[str] | None = None,
        exclude_rule_ids: Iterable[str] = (),
        exclude_categories: Iterable[str] = (),
        exclude_tags: Iterable[str] = (),
    ) -> None:
        object.__setattr__(
            self,
            "include_rule_ids",
            self._normalize_optional(
                include_rule_ids,
                "include_rule_ids",
            ),
        )
        object.__setattr__(
            self,
            "include_categories",
            self._normalize_optional(
                include_categories,
                "include_categories",
            ),
        )
        object.__setattr__(
            self,
            "include_tags",
            self._normalize_optional(
                include_tags,
                "include_tags",
            ),
        )
        object.__setattr__(
            self,
            "exclude_rule_ids",
            self._normalize_required(
                exclude_rule_ids,
                "exclude_rule_ids",
            ),
        )
        object.__setattr__(
            self,
            "exclude_categories",
            self._normalize_required(
                exclude_categories,
                "exclude_categories",
            ),
        )
        object.__setattr__(
            self,
            "exclude_tags",
            self._normalize_required(
                exclude_tags,
                "exclude_tags",
            ),
        )

    @classmethod
    def _normalize_optional(
        cls,
        values: Iterable[str] | None,
        field_name: str,
    ) -> frozenset[str] | None:
        if values is None:
            return None
        return cls._normalize_required(values, field_name)

    @staticmethod
    def _normalize_required(
        values: Iterable[str],
        field_name: str,
    ) -> frozenset[str]:
        normalized: set[str] = set()

        for value in values:
            if not isinstance(value, str) or not value.strip():
                raise RuleSelectionError(
                    f"{field_name} must not contain empty values"
                )
            normalized.add(value.strip())

        return frozenset(normalized)


class RuleSelector:
    """Translate user-facing criteria into executable rule plans."""

    def __init__(self, rules: Sequence[BaseRule]) -> None:
        self._rules = tuple(rules)
        self._registry = RuleRegistry(self._rules)

    @property
    def registry(self) -> RuleRegistry:
        """Return the metadata catalogue used for validation."""
        return self._registry

    def select(
        self,
        *,
        include_rule_ids: Iterable[str] | None = None,
        include_categories: Iterable[str] | None = None,
        include_tags: Iterable[str] | None = None,
        exclude_rule_ids: Iterable[str] = (),
        exclude_categories: Iterable[str] = (),
        exclude_tags: Iterable[str] = (),
        strict: bool = True,
    ) -> RuleExecutionPlan:
        """Build an immutable execution plan from selection criteria.

        Inclusion dimensions are combined by intersection. Within one
        dimension, matching any supplied value is sufficient. Exclusions are
        applied afterwards and always take precedence.
        """
        selection = RuleSelection(
            include_rule_ids=include_rule_ids,
            include_categories=include_categories,
            include_tags=include_tags,
            exclude_rule_ids=exclude_rule_ids,
            exclude_categories=exclude_categories,
            exclude_tags=exclude_tags,
        )

        if strict:
            self._validate_known_values(selection)

        rule_filter = self.as_filter(selection)
        return RuleExecutionPlan(
            tuple(
                rule
                for rule in self._rules
                if rule_filter.matches(rule)
            )
        )

    def as_filter(self, selection: RuleSelection) -> RuleFilter:
        """Translate a normalized selection into a low-level RuleFilter."""
        return RuleFilter(
            rule_ids=selection.include_rule_ids,
            categories=selection.include_categories,
            predicate=lambda rule: self._matches_tags_and_exclusions(
                rule,
                selection,
            ),
        )

    def _validate_known_values(
        self,
        selection: RuleSelection,
    ) -> None:
        known_rule_ids = set(self._registry.rule_ids)
        known_categories = set(self._registry.categories())
        known_tags = set(self._registry.tags())

        self._raise_unknown(
            "rule identifiers",
            self._all_values(
                selection.include_rule_ids,
                selection.exclude_rule_ids,
            ) - known_rule_ids,
        )
        self._raise_unknown(
            "categories",
            self._all_values(
                selection.include_categories,
                selection.exclude_categories,
            ) - known_categories,
        )
        self._raise_unknown(
            "tags",
            self._all_values(
                selection.include_tags,
                selection.exclude_tags,
            ) - known_tags,
        )

    @staticmethod
    def _all_values(
        included: frozenset[str] | None,
        excluded: frozenset[str],
    ) -> set[str]:
        return set(included or ()) | set(excluded)

    @staticmethod
    def _raise_unknown(
        label: str,
        unknown: set[str],
    ) -> None:
        if not unknown:
            return

        values = ", ".join(repr(value) for value in sorted(unknown))
        raise RuleSelectionError(f"Unknown {label}: {values}")

    @staticmethod
    def _matches_tags_and_exclusions(
        rule: BaseRule,
        selection: RuleSelection,
    ) -> bool:
        descriptor = rule.metadata
        tags = frozenset(descriptor.tags)

        if (
            selection.include_tags is not None
            and tags.isdisjoint(selection.include_tags)
        ):
            return False

        if descriptor.rule_id in selection.exclude_rule_ids:
            return False

        if descriptor.category in selection.exclude_categories:
            return False

        if not tags.isdisjoint(selection.exclude_tags):
            return False

        return True


__all__ = [
    "RuleSelection",
    "RuleSelectionError",
    "RuleSelector",
]
