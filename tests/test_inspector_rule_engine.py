"""Compatibility tests for Inspector using RuleEngine."""

from __future__ import annotations

import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.inspector import Inspector
from custom_components.ha_inspector.engine.models import Finding
from custom_components.ha_inspector.engine.rules.base import BaseRule
from custom_components.ha_inspector.engine.severity import Severity


class WarningRule(BaseRule):
    rule_id = "test.warning"
    category = "system"
    weight = 10

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        del context
        return [
            Finding(
                finding_id="TEST_WARNING",
                severity=Severity.WARNING,
                title="Test warning",
                description="Warning produced by the compatibility test.",
            )
        ]


class EmptyRule(BaseRule):
    rule_id = "test.empty"
    category = "versions"
    weight = 5

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        del context
        return []


class FailingRule(BaseRule):
    rule_id = "test.failure"
    category = "system"
    weight = 10

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        del context
        raise RuntimeError("expected failure")


@pytest.mark.asyncio
async def test_inspector_preserves_public_result_shape() -> None:
    inspector = Inspector(rules=[WarningRule(), EmptyRule()])

    result = await inspector.run(object())

    assert result.checks_executed == 2
    assert result.total_findings == 1
    assert result.score == 97
    assert result.categories == {
        "system": {
            "score": 97,
            "checks": 1,
            "findings": 1,
        },
        "versions": {
            "score": 100,
            "checks": 1,
            "findings": 0,
        },
    }
    assert result.metadata == {
        "collectors_executed": 0,
        "rules_discovered": 2,
        "rules_executed": 2,
        "diagnostics_included": False,
    }
    assert result.finished_at is not None


@pytest.mark.asyncio
async def test_inspector_preserves_diagnostics_catalog() -> None:
    inspector = Inspector(rules=[WarningRule()])

    result = await inspector.run(object(), diagnostics=True)

    assert result.metadata["diagnostics_included"] is True
    assert result.metadata["rules"] == [WarningRule().metadata.as_dict()]
    assert result.metadata["context"] == {
        "system": {},
        "storage": {},
        "recorder": {},
        "integrations": {},
        "entities": {},
    }


@pytest.mark.asyncio
async def test_inspector_isolates_rule_failure_and_continues() -> None:
    inspector = Inspector(rules=[FailingRule(), WarningRule()])

    result = await inspector.run(object())

    assert result.checks_executed == 1
    assert result.metadata["rules_executed"] == 1
    assert result.total_findings == 1
    assert result.findings[0].finding_id == "TEST_WARNING"

    execution = inspector._rule_engine.execution_context
    assert execution is not None
    assert execution.rules_executed == 2
    assert execution.rules_succeeded == 1
    assert execution.rules_failed == 1
