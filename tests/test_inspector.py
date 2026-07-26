"""Tests for the HA Inspector orchestrator."""

from __future__ import annotations

from custom_components.ha_inspector.engine.collectors.base import BaseCollector
from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.inspector import Inspector
from custom_components.ha_inspector.engine.models import Finding
from custom_components.ha_inspector.engine.rules.base import BaseRule
from custom_components.ha_inspector.engine.severity import Severity


class ContextCollector(BaseCollector):
    """Populate the inspection context."""

    collector_id = "test.context"

    async def collect(self, hass, context: InspectionContext) -> None:
        context.system["installation_type"] = "Home Assistant OS"
        context.system["latitude"] = 41.0


class FailingCollector(BaseCollector):
    """Collector used to verify error isolation."""

    collector_id = "test.failing_collector"

    async def collect(self, hass, context: InspectionContext) -> None:
        raise RuntimeError("collector failed")


class HealthyRule(BaseRule):
    """Return findings in an intentionally unsorted order."""

    rule_id = "system.healthy"
    title = "Healthy rule"
    category = "system"
    severity = Severity.INFO
    weight = 10

    async def check(self, context: InspectionContext) -> list[Finding]:
        assert context.system["installation_type"] == "Home Assistant OS"
        return [
            Finding(
                finding_id="warning.finding",
                severity=Severity.WARNING,
                title="Warning",
                description="Warning finding",
            ),
            Finding(
                finding_id="critical.finding",
                severity=Severity.CRITICAL,
                title="Critical",
                description="Critical finding",
            ),
        ]


class FailingRule(BaseRule):
    """Rule used to verify error isolation."""

    rule_id = "system.failing"
    title = "Failing rule"
    category = "system"
    severity = Severity.ERROR
    weight = 10

    async def check(self, context: InspectionContext) -> list[Finding]:
        raise ValueError("rule failed")


async def test_run_executes_collectors_rules_and_sorts_findings() -> None:
    inspector = Inspector(
        collectors=[ContextCollector()],
        rules=[HealthyRule()],
    )

    result = await inspector.run(object())

    assert result.finished_at is not None
    assert result.checks_executed == 1
    assert result.metadata["collectors_executed"] == 1
    assert result.metadata["rules_discovered"] == 1
    assert result.metadata["rules_executed"] == 1
    assert [finding.finding_id for finding in result.findings] == [
        "critical.finding",
        "warning.finding",
    ]


async def test_run_continues_after_component_errors() -> None:
    inspector = Inspector(
        collectors=[FailingCollector(), ContextCollector()],
        rules=[FailingRule(), HealthyRule()],
    )

    result = await inspector.run(object())

    assert result.checks_executed == 1
    assert result.metadata["rules_executed"] == 1
    assert result.metadata["execution_errors"] == [
        {
            "type": "collector",
            "id": "test.failing_collector",
            "error": "RuntimeError",
            "message": "collector failed",
        },
        {
            "type": "rule",
            "id": "system.failing",
            "error": "ValueError",
            "message": "rule failed",
        },
    ]


async def test_run_diagnostics_filters_sensitive_system_data() -> None:
    inspector = Inspector(
        collectors=[ContextCollector()],
        rules=[HealthyRule()],
    )

    result = await inspector.run(object(), diagnostics=True)

    assert result.metadata["diagnostics_included"] is True
    assert result.metadata["context"]["system"] == {
        "installation_type": "Home Assistant OS"
    }
    assert result.metadata["rules"][0]["rule_id"] == "system.healthy"
