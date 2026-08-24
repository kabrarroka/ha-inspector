"""Tests for the HA Inspector orchestrator."""

from __future__ import annotations

from types import ModuleType, SimpleNamespace

import pytest

from custom_components.ha_inspector.engine.collectors.base import BaseCollector
from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.inspector import Inspector
from custom_components.ha_inspector.engine.models import Finding
from custom_components.ha_inspector.engine.registry import EngineRegistry
from custom_components.ha_inspector.engine.request import InspectionRequest
from custom_components.ha_inspector.engine.rules.base import BaseRule


class RecordingCollector(BaseCollector):
    collector_id = "recording"

    def __init__(self) -> None:
        self.calls = 0

    async def collect(self, hass, context: InspectionContext) -> None:
        del hass
        self.calls += 1
        context.metadata["collected"] = True


class AlphaRule(BaseRule):
    rule_id = "alpha.rule"
    title = "Alpha rule"
    category = "system"
    tags = ("alpha",)

    async def check(self, context: InspectionContext) -> list[Finding]:
        assert context.metadata["collected"] is True
        return []


class BetaRule(BaseRule):
    rule_id = "beta.rule"
    title = "Beta rule"
    category = "entities"
    tags = ("beta",)

    async def check(self, context: InspectionContext) -> list[Finding]:
        del context
        return []


def _module_with(name: str, *classes: type) -> ModuleType:
    module = ModuleType(name)

    for candidate in classes:
        candidate.__module__ = module.__name__
        setattr(module, candidate.__name__, candidate)

    return module


@pytest.mark.asyncio
async def test_run_executes_collectors_and_selected_rules() -> None:
    collector = RecordingCollector()

    inspector = Inspector(
        collectors=[collector],
        rules=[AlphaRule(), BetaRule()],
    )

    request = InspectionRequest(
        include_rule_ids=("alpha.rule",),
    )

    result = await inspector.run(
        object(),
        request=request,
    )

    assert collector.calls == 1
    assert result.checks_executed == 1

    assert result.metadata["collectors_executed"] == 1
    assert result.metadata["rules_discovered"] == 2
    assert result.metadata["rules_selected"] == 1

    assert result.metadata["request"] == request.as_dict()
    assert result.metadata["diagnostics_included"] is False

    execution_plan = result.metadata["execution_plan"]
    assert execution_plan["rule_ids"] == ["alpha.rule"]

    assert "rules" not in result.metadata
    assert "context" not in result.metadata


@pytest.mark.asyncio
async def test_run_diagnostics_override_includes_diagnostics() -> None:
    inspector = Inspector(
        rules=[AlphaRule(), BetaRule()],
    )

    request = InspectionRequest(
        include_rule_ids=("alpha.rule",),
        diagnostics=False,
    )

    result = await inspector.run(
        object(),
        request=request,
        diagnostics=True,
    )

    assert result.metadata["diagnostics_included"] is True

    request_data = result.metadata["request"]
    assert request_data["diagnostics"] is True
    assert request_data["include_rule_ids"] == ["alpha.rule"]

    rules = result.metadata["rules"]

    assert [rule["rule_id"] for rule in rules] == [
        "alpha.rule",
        "beta.rule",
    ]

    context = result.metadata["context"]

    assert set(context) == {
        "system",
        "storage",
        "logs",
        "addons",
        "repairs",
        "backups",
        "recorder",
        "integrations",
        "entities",
    }


@pytest.mark.asyncio
async def test_run_uses_default_request() -> None:
    inspector = Inspector()

    result = await inspector.run(object())

    assert result.checks_executed == 0
    assert result.metadata["rules_discovered"] == 0
    assert result.metadata["rules_selected"] == 0
    assert result.metadata["diagnostics_included"] is False

    assert result.metadata["request"] == InspectionRequest().as_dict()


def test_from_registry_uses_registered_collectors_and_rules() -> None:
    registry = EngineRegistry()

    registry._register_from_module(
        _module_with("tests.inspector_collectors", RecordingCollector),
        BaseCollector,
    )
    registry._register_from_module(
        _module_with("tests.inspector_rules", AlphaRule),
        BaseRule,
    )

    inspector = Inspector.from_registry(registry)

    assert len(inspector._collectors) == 1
    assert len(inspector._rules) == 1
    assert inspector._collectors[0].collector_id == "recording"
    assert inspector._rules[0].rule_id == "alpha.rule"


@pytest.mark.asyncio
async def test_run_uses_home_assistant_language() -> None:
    hass = SimpleNamespace(
        config=SimpleNamespace(language="es-ES"),
    )

    inspector = Inspector()

    result = await inspector.run(hass)  # type: ignore[arg-type]

    assert result.metadata["language"] == "es"


@pytest.mark.asyncio
async def test_run_request_language_overrides_home_assistant() -> None:
    hass = SimpleNamespace(
        config=SimpleNamespace(language="en"),
    )

    inspector = Inspector()

    result = await inspector.run(
        hass,  # type: ignore[arg-type]
        request=InspectionRequest(language="es"),
    )

    assert result.metadata["language"] == "es"


@pytest.mark.asyncio
async def test_run_applies_finding_suppression_policy() -> None:
    """Inspector passes finding suppression through to the rule engine."""
    from custom_components.ha_inspector.engine.severity import Severity
    from custom_components.ha_inspector.engine.suppression import (
        FindingSuppressionPolicy,
    )

    class FindingRule(BaseRule):
        rule_id = "finding.rule"
        title = "Finding rule"
        category = "system"
        tags = ("finding",)
        weight = 20

        async def check(
            self,
            context: InspectionContext,
        ) -> list[Finding]:
            del context
            return [
                Finding(
                    finding_id="FINDING_SUPPRESSED",
                    severity=Severity.ERROR,
                    title="Suppressed finding",
                    description="Suppressed finding",
                )
            ]

    inspector = Inspector(rules=[FindingRule()])

    result = await inspector.run(
        object(),
        request=InspectionRequest(
            include_rule_ids=("finding.rule",),
        ),
        suppression=FindingSuppressionPolicy(
            finding_ids=frozenset({"FINDING_SUPPRESSED"})
        ),
    )

    assert result.checks_executed == 1
    assert result.total_findings == 0
    assert result.score == 100
    assert result.metadata["suppressed_findings"] == [
        "FINDING_SUPPRESSED"
    ]
    assert result.metadata["suppressed_findings_count"] == 1


class FakeClock:
    """Return deterministic monotonic timestamps."""

    def __init__(self, *values: float) -> None:
        self._values = iter(values)

    def __call__(self) -> float:
        return next(self._values)


@pytest.mark.asyncio
async def test_run_records_inspection_and_collector_timings() -> None:
    """Inspector exposes deterministic operational timing metrics."""
    collector = RecordingCollector()
    inspector = Inspector(
        collectors=[collector],
        rules=[AlphaRule()],
        clock=FakeClock(
            10.0,  # inspection start
            10.1,  # collectors start
            10.2,  # collector start
            10.5,  # collector end
            10.6,  # collectors end
            10.7,  # rules start
            11.1,  # rules end
            11.2,  # inspection end
        ),
    )

    result = await inspector.run(object())

    assert result.metadata["timings"] == {
        "inspection_seconds": pytest.approx(1.2),
        "collectors_seconds": pytest.approx(0.5),
        "rules_seconds": pytest.approx(0.4),
        "collectors": {
            "recording": pytest.approx(0.3),
        },
    }


@pytest.mark.asyncio
async def test_run_records_empty_collector_timings() -> None:
    """Inspector exposes timing metrics when no collectors are registered."""
    inspector = Inspector(
        clock=FakeClock(
            20.0,  # inspection start
            20.1,  # collectors start
            20.2,  # collectors end
            20.3,  # rules start
            20.4,  # rules end
            20.5,  # inspection end
        ),
    )

    result = await inspector.run(object())

    assert result.metadata["timings"] == {
        "inspection_seconds": pytest.approx(0.5),
        "collectors_seconds": pytest.approx(0.1),
        "rules_seconds": pytest.approx(0.1),
        "collectors": {},
    }
