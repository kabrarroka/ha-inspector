"""Execution engine for selected HA Inspector rules."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from .context import InspectionContext
from .models import Finding
from .result import InspectionResult
from .rule_selector import RuleExecutionPlan
from .rules.base import BaseRule
from .severity import Severity

_LOGGER = logging.getLogger(__name__)


class RuleEngineError(RuntimeError):
    """Raised when the rule engine cannot be built safely."""


class RuleEngine:
    """Execute rules selected by an immutable execution plan."""

    def __init__(self, rules: Sequence[BaseRule]) -> None:
        """Initialize the engine with available rule instances."""
        self._rules: dict[str, BaseRule] = {}

        for rule in rules:
            rule_id = rule.metadata.rule_id

            if rule_id in self._rules:
                raise RuleEngineError(
                    f"Duplicate rule identifier: {rule_id}"
                )

            self._rules[rule_id] = rule

    @property
    def rule_ids(self) -> tuple[str, ...]:
        """Return available rule identifiers in deterministic order."""
        return tuple(sorted(self._rules))

    def get_rule(self, rule_id: str) -> BaseRule:
        """Return a registered rule.

        Raises:
            KeyError: If the rule identifier is unknown.
        """
        return self._rules[rule_id]

    async def execute(
        self,
        context: InspectionContext,
        plan: RuleExecutionPlan,
    ) -> InspectionResult:
        """Execute every rule included in the execution plan."""
        self._validate_plan(plan)

        result = InspectionResult()
        execution_errors: list[str] = []

        for rule_id in plan:
            rule = self._rules[rule_id]
            descriptor = rule.metadata

            try:
                findings = await rule.check(context)
            except Exception as err:
                _LOGGER.exception(
                    "Unexpected error executing HA Inspector rule %s",
                    rule_id,
                )

                execution_errors.append(rule_id)
                findings = [
                    Finding(
                        finding_id=f"{rule_id}.execution_error",
                        severity=Severity.ERROR,
                        title=f"Rule execution failed: {descriptor.title}",
                        description=(
                            f"The rule {rule_id!r} could not be executed: "
                            f"{type(err).__name__}: {err}"
                        ),
                        recommendation=(
                            "Review the Home Assistant logs and the rule "
                            "implementation."
                        ),
                        data={
                            "rule_id": rule_id,
                            "exception_type": type(err).__name__,
                        },
                    )
                ]

            result.record_rule(
                category=descriptor.category,
                weight=descriptor.weight,
                findings=findings,
            )

        result.metadata["rules_available"] = len(self._rules)
        result.metadata["rules_selected"] = len(plan)
        result.metadata["execution_errors"] = execution_errors
        result.finish()

        return result

    def _validate_plan(self, plan: RuleExecutionPlan) -> None:
        """Raise KeyError when the plan references an unknown rule."""
        for rule_id in plan:
            if rule_id not in self._rules:
                raise KeyError(rule_id)


__all__ = [
    "RuleEngine",
    "RuleEngineError",
]
