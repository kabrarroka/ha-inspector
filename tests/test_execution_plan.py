"""Tests for immutable rule execution plans."""

from __future__ import annotations

import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.execution_plan import (
    RuleExecutionPlan,
)
from custom_components.ha_inspector.engine.models import Finding
from custom_components.ha_inspector.engine.rule_engine import RuleEngine
from custom_components.ha_inspector.engine.rule_filter import RuleFilter
from custom_components.ha_inspector.engine.rules.base import BaseRule


class SystemAlphaRule(BaseRule):
    rule_id = "system.alpha"
    category = "system"

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        del context
        return []


class VersionBetaRule(BaseRule):
    rule_id = "versions.beta"
    category = "versions"

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        del context
        return []


class SystemGammaRule(BaseRule):
    rule_id = "system.gamma"
    category = "system"

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        del context
        return []


def make_rules() -> list[BaseRule]:
    """Return rules in deterministic declaration order."""
    return [
        SystemAlphaRule(),
        VersionBetaRule(),
        SystemGammaRule(),
    ]


def test_plan_freezes_source_sequence() -> None:
    rules = make_rules()
    plan = RuleExecutionPlan(rules)

    rules.clear()

    assert plan.rule_ids == (
        "system.alpha",
        "versions.beta",
        "system.gamma",
    )
    assert len(plan) == 3


def test_plan_exposes_ordered_metadata() -> None:
    plan = RuleExecutionPlan(make_rules())

    assert plan.rule_ids == (
        "system.alpha",
        "versions.beta",
        "system.gamma",
    )
    assert plan.categories == ("system", "versions")
    assert plan.is_empty is False


def test_empty_plan_reports_empty_state() -> None:
    plan = RuleExecutionPlan([])

    assert tuple(plan) == ()
    assert plan.rule_ids == ()
    assert plan.categories == ()
    assert len(plan) == 0
    assert plan.is_empty is True


def test_engine_builds_unfiltered_plan() -> None:
    engine = RuleEngine(make_rules())

    plan = engine.build_plan()

    assert plan.rule_ids == (
        "system.alpha",
        "versions.beta",
        "system.gamma",
    )


def test_engine_builds_filtered_plan_in_declaration_order() -> None:
    engine = RuleEngine(make_rules())

    plan = engine.build_plan(
        RuleFilter(
            rule_ids={
                "system.gamma",
                "system.alpha",
            }
        )
    )

    assert plan.rule_ids == (
        "system.alpha",
        "system.gamma",
    )


def test_select_rules_remains_compatible() -> None:
    engine = RuleEngine(make_rules())

    selected = engine.select_rules(
        RuleFilter(categories={"versions"})
    )

    assert isinstance(selected, tuple)
    assert [rule.metadata.rule_id for rule in selected] == [
        "versions.beta",
    ]


@pytest.mark.asyncio
async def test_run_exposes_generated_execution_plan() -> None:
    engine = RuleEngine(make_rules())

    results = await engine.run(
        InspectionContext(),
        rule_filter=RuleFilter(categories={"system"}),
    )

    assert [result.rule_id for result in results] == [
        "system.alpha",
        "system.gamma",
    ]
    assert engine.execution_plan is not None
    assert engine.execution_plan.rule_ids == (
        "system.alpha",
        "system.gamma",
    )


@pytest.mark.asyncio
async def test_engine_executes_prebuilt_plan() -> None:
    engine = RuleEngine(make_rules())
    plan = RuleExecutionPlan(
        [
            SystemGammaRule(),
            VersionBetaRule(),
        ]
    )

    results = await engine.run_plan(
        InspectionContext(),
        plan,
    )

    assert [result.rule_id for result in results] == [
        "system.gamma",
        "versions.beta",
    ]
    assert engine.execution_plan is plan

    execution = engine.execution_context
    assert execution is not None
    assert execution.total_rules == 2
    assert execution.rules_executed == 2
    assert execution.progress == 1.0
