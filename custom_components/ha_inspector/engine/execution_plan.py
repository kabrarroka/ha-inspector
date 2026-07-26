"""Immutable execution plans for HA Inspector rules."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass

from .rules.base import BaseRule


@dataclass(frozen=True, slots=True)
class RuleExecutionPlan:
    """An immutable, ordered collection of rules to execute."""

    rules: tuple[BaseRule, ...]

    def __init__(self, rules: Sequence[BaseRule]) -> None:
        """Freeze the supplied rule sequence."""
        object.__setattr__(self, "rules", tuple(rules))

    def __len__(self) -> int:
        """Return the number of planned rules."""
        return len(self.rules)

    def __iter__(self) -> Iterator[BaseRule]:
        """Iterate over planned rules in execution order."""
        return iter(self.rules)

    @property
    def rule_ids(self) -> tuple[str, ...]:
        """Return planned rule identifiers in execution order."""
        return tuple(rule.metadata.rule_id for rule in self.rules)

    @property
    def categories(self) -> tuple[str, ...]:
        """Return unique categories in first-appearance order."""
        return tuple(
            dict.fromkeys(
                rule.metadata.category
                for rule in self.rules
            )
        )

    @property
    def is_empty(self) -> bool:
        """Return whether the plan contains no rules."""
        return not self.rules
