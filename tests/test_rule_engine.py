from __future__ import annotations

from dataclasses import dataclass

import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.models import Finding
from custom_components.ha_inspector.engine.result import InspectionResult
from custom_components.ha_inspector.engine.rule_engine import (
    RuleEngine,
    RuleEngineError,
)
from custom_components.ha_inspector.engine.rule_selector import RuleExecutionPlan
from custom_components.ha_inspector.engine.rules.base import (
    CompatibilityRuleDescriptor,
)
from custom_components.ha_inspector.engine.severity import Severity


@dataclass(frozen=True)
class FakeRule:
    metadata: CompatibilityRuleDescriptor
    findings: list[Finding]

    async def check(self, context: InspectionContext) -> list[Finding]:
        return self.findings

@dataclass(frozen=True)
class ExplodingRule:
    metadata: CompatibilityRuleDescriptor

    async def check(self, context: InspectionContext) -> list[Finding]:
        raise RuntimeError("boom")


def descriptor(rule_id: str) -> CompatibilityRuleDescriptor:
    return CompatibilityRuleDescriptor(
        rule_id=rule_id,
        title=rule_id,
        category="system",
        severity=Severity.INFO,
        tags=(),
        weight=1,
    )


def finding(rule_id: str) -> Finding:
    return Finding(
        finding_id=f"{rule_id}.1",
        severity=Severity.WARNING,
        title="warning",
        description="warning",
    )


@pytest.mark.asyncio
async def test_execute_empty_plan():
    engine = RuleEngine([])

    result = await engine.execute(
        InspectionContext(),
        RuleExecutionPlan(()),
    )

    assert isinstance(result, InspectionResult)
    assert result.checks_executed == 0
    assert result.total_findings == 0


@pytest.mark.asyncio
async def test_execute_single_rule():
    rule = FakeRule(
        descriptor("RULE1"),
        [finding("RULE1")],
    )

    engine = RuleEngine([rule])

    result = await engine.execute(
        InspectionContext(),
        RuleExecutionPlan(("RULE1",)),
    )

    assert result.checks_executed == 1
    assert result.total_findings == 1


@pytest.mark.asyncio
async def test_unknown_rule():
    engine = RuleEngine([])

    with pytest.raises(KeyError):
        await engine.execute(
            InspectionContext(),
            RuleExecutionPlan(("UNKNOWN",)),
        )


@pytest.mark.asyncio
async def test_rule_exception_becomes_finding():
    engine = RuleEngine(
        [
            ExplodingRule(
                descriptor("BROKEN"),
            )
        ]
    )

    result = await engine.execute(
        InspectionContext(),
        RuleExecutionPlan(("BROKEN",)),
    )

    assert result.checks_executed == 1
    assert result.total_findings == 1

    generated = result.findings[0]

    assert generated.severity is Severity.ERROR
    assert generated.finding_id == "BROKEN.execution_error"

    assert result.metadata["execution_errors"] == ["BROKEN"]


def test_duplicate_rule_registration():
    rule = FakeRule(
        descriptor("RULE1"),
        [],
    )

    with pytest.raises(RuleEngineError):
        RuleEngine([rule, rule])

def test_rule_ids_are_sorted() -> None:
    first = FakeRule(
        descriptor("B_RULE"),
        [],
    )
    second = FakeRule(
        descriptor("A_RULE"),
        [],
    )

    engine = RuleEngine([first, second])

    assert engine.rule_ids == ("A_RULE", "B_RULE")


def test_get_rule_returns_registered_instance() -> None:
    rule = FakeRule(
        descriptor("RULE1"),
        [],
    )

    engine = RuleEngine([rule])

    assert engine.get_rule("RULE1") is rule