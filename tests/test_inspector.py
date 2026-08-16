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
