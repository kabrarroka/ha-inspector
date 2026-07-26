"""Independent rule execution engine for HA Inspector."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from time import perf_counter
from typing import TypeAlias

from .context import InspectionContext
from .execution_context import ExecutionContext
from .execution_plan import RuleExecutionPlan
from .result import RuleExecutionResult
from .rule_filter import RuleFilter
from .rules.base import BaseRule

Clock: TypeAlias = Callable[[], float]


class RuleEngine:
    """Plan and execute inspection rules independently from Inspector."""

    def __init__(
        self,
        rules: Sequence[BaseRule],
        *,
        clock: Clock = perf_counter,
    ) -> None:
        self._rules = tuple(rules)
        self._clock = clock
        self._execution_context: ExecutionContext | None = None
        self._execution_plan: RuleExecutionPlan | None = None

    @property
    def rules(self) -> tuple[BaseRule, ...]:
        """Return the configured rules as an immutable sequence."""
        return self._rules

    @property
    def execution_context(self) -> ExecutionContext | None:
        """Return the state of the most recent execution."""
        return self._execution_context

    @property
    def execution_plan(self) -> RuleExecutionPlan | None:
        """Return the plan used by the most recent execution."""
        return self._execution_plan

    def select_rules(
        self,
        rule_filter: RuleFilter | None = None,
    ) -> tuple[BaseRule, ...]:
        """Return selected rules while preserving declaration order."""
        return self.build_plan(rule_filter).rules

    def build_plan(
        self,
        rule_filter: RuleFilter | None = None,
    ) -> RuleExecutionPlan:
        """Build an immutable plan from the configured rules."""
        if rule_filter is None:
            return RuleExecutionPlan(self._rules)

        return RuleExecutionPlan(
            tuple(
                rule
                for rule in self._rules
                if rule_filter.matches(rule)
            )
        )

    async def run(
        self,
        context: InspectionContext,
        *,
        rule_filter: RuleFilter | None = None,
    ) -> tuple[RuleExecutionResult, ...]:
        """Build and execute a rule plan."""
        plan = self.build_plan(rule_filter)
        return await self.run_plan(context, plan)

    async def run_plan(
        self,
        context: InspectionContext,
        plan: RuleExecutionPlan,
    ) -> tuple[RuleExecutionResult, ...]:
        """Execute a previously built plan in its declared order."""
        self._execution_plan = plan
        execution = ExecutionContext(
            total_rules=len(plan),
            clock=self._clock,
        )
        self._execution_context = execution
        results: list[RuleExecutionResult] = []

        for rule in plan:
            results.append(
                await self._execute_rule(
                    rule,
                    context,
                    execution,
                )
            )

        execution.finish()
        return tuple(results)

    async def _execute_rule(
        self,
        rule: BaseRule,
        context: InspectionContext,
        execution: ExecutionContext,
    ) -> RuleExecutionResult:
        """Execute one rule and capture its outcome."""
        descriptor = rule.metadata
        execution.start_rule(descriptor.rule_id)

        try:
            findings = tuple(await rule.check(context))
        except Exception as err:  # noqa: BLE001 - rule isolation is intentional
            duration_ms = execution.complete_rule(success=False)
            return RuleExecutionResult(
                rule_id=descriptor.rule_id,
                duration_ms=duration_ms,
                success=False,
                error=f"{type(err).__name__}: {err}",
            )

        duration_ms = execution.complete_rule(success=True)
        return RuleExecutionResult(
            rule_id=descriptor.rule_id,
            duration_ms=duration_ms,
            findings=findings,
        )
