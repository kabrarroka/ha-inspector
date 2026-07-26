"""Tests for the independent rule engine."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.models import Finding
from custom_components.ha_inspector.engine.rule_engine import RuleEngine
from custom_components.ha_inspector.engine.rules.base import BaseRule
from custom_components.ha_inspector.engine.severity import Severity


class SequenceClock:
    """Return deterministic monotonic values."""

    def __init__(self, *values: float) -> None:
        self._values: Iterator[float] = iter(values)

    def __call__(self) -> float:
        return next(self._values)


class SuccessfulRule(BaseRule):
    rule_id = "test.success"
    category = "test"

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        del context
        return [
            Finding(
                finding_id="TEST_FINDING",
                severity=Severity.WARNING,
                title="Test finding",
                description="Finding produced by the successful test rule.",
            )
        ]


class EmptyRule(BaseRule):
    rule_id = "test.empty"
    category = "test"

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        del context
        return []


class FailingRule(BaseRule):
    rule_id = "test.failure"
    category = "test"

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        del context
        raise RuntimeError("expected failure")


@pytest.mark.asyncio
async def test_engine_executes_rules_in_declaration_order() -> None:
    engine = RuleEngine(
        [SuccessfulRule(), EmptyRule()],
        clock=SequenceClock(
            1.0,    # execution start
            1.1,    # first rule start
            1.101,  # first rule end
            2.0,    # second rule start
            2.002,  # second rule end
            2.01,   # execution finish
        ),
    )

    executions = await engine.run(InspectionContext())

    assert [execution.rule_id for execution in executions] == [
        "test.success",
        "test.empty",
    ]
    assert executions[0].finding_count == 1
    assert executions[1].finding_count == 0


@pytest.mark.asyncio
async def test_engine_measures_each_rule_duration() -> None:
    engine = RuleEngine(
        [SuccessfulRule()],
        clock=SequenceClock(
            10.0,
            10.1,
            10.125,
            10.2,
        ),
    )

    executions = await engine.run(InspectionContext())

    assert executions[0].duration_ms == pytest.approx(25.0)


@pytest.mark.asyncio
async def test_failed_rule_does_not_stop_following_rules() -> None:
    engine = RuleEngine(
        [FailingRule(), EmptyRule()],
        clock=SequenceClock(
            1.0,
            1.1,
            1.101,
            2.0,
            2.001,
            2.01,
        ),
    )

    executions = await engine.run(InspectionContext())

    assert len(executions) == 2
    assert executions[0].success is False
    assert executions[0].error == "RuntimeError: expected failure"
    assert executions[1].success is True


def test_rules_property_is_immutable_snapshot() -> None:
    rules = [EmptyRule()]
    engine = RuleEngine(rules)

    rules.append(SuccessfulRule())

    assert len(engine.rules) == 1
    assert isinstance(engine.rules, tuple)


@pytest.mark.asyncio
async def test_empty_engine_returns_empty_tuple() -> None:
    engine = RuleEngine(
        [],
        clock=SequenceClock(1.0, 1.001),
    )

    executions = await engine.run(InspectionContext())

    assert executions == ()


@pytest.mark.asyncio
async def test_engine_exposes_completed_execution_context() -> None:
    engine = RuleEngine(
        [SuccessfulRule(), FailingRule()],
        clock=SequenceClock(
            5.0,
            5.1,
            5.11,
            5.2,
            5.23,
            5.3,
        ),
    )

    await engine.run(InspectionContext())

    execution = engine.execution_context
    assert execution is not None
    assert execution.is_running is False
    assert execution.rules_executed == 2
    assert execution.rules_succeeded == 1
    assert execution.rules_failed == 1
    assert execution.progress == 1.0
    assert execution.duration_ms == pytest.approx(300.0)


@pytest.mark.asyncio
async def test_each_run_creates_a_new_execution_context() -> None:
    engine = RuleEngine(
        [],
        clock=SequenceClock(
            1.0,
            1.01,
            2.0,
            2.02,
        ),
    )

    await engine.run(InspectionContext())
    first_execution = engine.execution_context

    await engine.run(InspectionContext())
    second_execution = engine.execution_context

    assert first_execution is not None
    assert second_execution is not None
    assert second_execution is not first_execution
    assert first_execution.duration_ms == pytest.approx(10.0)
    assert second_execution.duration_ms == pytest.approx(20.0)
