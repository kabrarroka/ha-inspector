"""Tests for the automatic HA Inspector engine registry."""

from types import ModuleType

import pytest

from custom_components.ha_inspector.engine.collectors.base import BaseCollector
from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.models import Finding
from custom_components.ha_inspector.engine.registry import EngineRegistry, RegistryError
from custom_components.ha_inspector.engine.rules.base import BaseRule


class AlphaCollector(BaseCollector):
    collector_id = "alpha"

    async def collect(self, hass, context: InspectionContext) -> None:
        del hass, context


class BetaCollector(BaseCollector):
    collector_id = "beta"

    async def collect(self, hass, context: InspectionContext) -> None:
        del hass, context


class AlphaRule(BaseRule):
    rule_id = "alpha.rule"

    async def check(self, context: InspectionContext) -> list[Finding]:
        del context
        return []


def _module_with(*classes: type) -> ModuleType:
    module = ModuleType("tests.dynamic_registry_module")
    for candidate in classes:
        candidate.__module__ = module.__name__
        setattr(module, candidate.__name__, candidate)
    return module


def test_registry_registers_collectors_and_rules() -> None:
    registry = EngineRegistry()

    registry._register_from_module(_module_with(BetaCollector, AlphaCollector), BaseCollector)
    registry._register_from_module(_module_with(AlphaRule), BaseRule)

    assert registry.collector_ids == ("alpha", "beta")
    assert registry.rule_ids == ("alpha.rule",)
    assert [collector.collector_id for collector in registry.create_collectors()] == [
        "alpha",
        "beta",
    ]
    assert [rule.rule_id for rule in registry.create_rules()] == ["alpha.rule"]


def test_registry_returns_fresh_instances() -> None:
    registry = EngineRegistry()
    registry._register_from_module(_module_with(AlphaCollector), BaseCollector)

    first = registry.create_collectors()
    second = registry.create_collectors()

    assert first[0] is not second[0]


def test_registry_rejects_duplicate_identifiers() -> None:
    duplicate = type(
        "DuplicateCollector",
        (BaseCollector,),
        {
            "collector_id": "alpha",
            "collect": AlphaCollector.collect,
        },
    )

    registry = EngineRegistry()
    registry._register_from_module(_module_with(AlphaCollector), BaseCollector)

    with pytest.raises(RegistryError, match="Duplicate identifier"):
        registry._register_from_module(_module_with(duplicate), BaseCollector)


def test_registry_rejects_blank_identifier() -> None:
    invalid = type(
        "InvalidCollector",
        (BaseCollector,),
        {
            "collector_id": " ",
            "collect": AlphaCollector.collect,
        },
    )

    registry = EngineRegistry()

    with pytest.raises(RegistryError, match="valid identifier"):
        registry._register_from_module(_module_with(invalid), BaseCollector)
