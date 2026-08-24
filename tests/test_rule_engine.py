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

@pytest.mark.asyncio
async def test_engine_uses_rule_id_for_execution_plan() -> None:
    """Execute catalogued rules using their public rule identifier."""
    from custom_components.ha_inspector.engine.context import InspectionContext
    from custom_components.ha_inspector.engine.rule_selector import (
        RuleExecutionPlan,
    )
    from custom_components.ha_inspector.engine.rules.backup_age import (
        BackupAgeRule,
    )

    engine = RuleEngine([BackupAgeRule()])

    assert engine.rule_ids == ("BACKUP_AGE",)

    plan = RuleExecutionPlan(("BACKUP_AGE",))

    result = await engine.execute(
        InspectionContext(),
        plan,
    )

    assert result.checks_executed == 1


@pytest.mark.asyncio
async def test_suppressed_finding_does_not_affect_result() -> None:
    """Suppressed findings remain outside active result scoring."""
    from custom_components.ha_inspector.engine.suppression import (
        FindingSuppressionPolicy,
    )

    rule = FakeRule(
        descriptor("RULE1"),
        [
            finding("RULE1"),
            Finding(
                finding_id="RULE1.2",
                severity=Severity.ERROR,
                title="error",
                description="error",
            ),
        ],
    )
    engine = RuleEngine([rule])

    result = await engine.execute(
        InspectionContext(),
        RuleExecutionPlan(("RULE1",)),
        suppression=FindingSuppressionPolicy(
            finding_ids=frozenset({"RULE1.1"})
        ),
    )

    assert result.checks_executed == 1
    assert [item.finding_id for item in result.findings] == ["RULE1.2"]
    assert result.total_findings == 1
    assert result.metadata["suppressed_findings"] == ["RULE1.1"]
    assert result.metadata["suppressed_findings_count"] == 1


@pytest.mark.asyncio
async def test_default_execution_suppresses_nothing() -> None:
    """Default execution preserves existing finding behaviour."""
    rule = FakeRule(
        descriptor("RULE1"),
        [finding("RULE1")],
    )
    engine = RuleEngine([rule])

    result = await engine.execute(
        InspectionContext(),
        RuleExecutionPlan(("RULE1",)),
    )

    assert result.total_findings == 1
    assert result.metadata["suppressed_findings"] == []
    assert result.metadata["suppressed_findings_count"] == 0


@pytest.mark.asyncio
async def test_fully_suppressed_rule_still_counts_as_executed() -> None:
    """A fully suppressed rule remains an executed healthy check."""
    from custom_components.ha_inspector.engine.suppression import (
        FindingSuppressionPolicy,
    )

    rule = FakeRule(
        descriptor("RULE1"),
        [finding("RULE1")],
    )
    engine = RuleEngine([rule])

    result = await engine.execute(
        InspectionContext(),
        RuleExecutionPlan(("RULE1",)),
        suppression=FindingSuppressionPolicy(
            finding_ids=frozenset({"RULE1.1"})
        ),
    )

    assert result.checks_executed == 1
    assert result.total_findings == 0
    assert result.score == 100
    assert result.categories["system"]["checks"] == 1
    assert result.categories["system"]["findings"] == 0
    assert result.metadata["suppressed_findings"] == ["RULE1.1"]
    assert result.metadata["suppressed_findings_count"] == 1
