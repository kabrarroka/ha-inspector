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

    registry._register_from_module(
        _module_with(BetaCollector, AlphaCollector),
        BaseCollector,
    )
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

def test_registry_compatibility_properties_return_instances() -> None:
    registry = EngineRegistry()
    registry._register_from_module(_module_with(AlphaCollector), BaseCollector)
    registry._register_from_module(_module_with(AlphaRule), BaseRule)

    collectors = registry.collectors
    rules = registry.rules

    assert [collector.collector_id for collector in collectors] == ["alpha"]
    assert [rule.rule_id for rule in rules] == ["alpha.rule"]


def test_registry_rejects_rule_with_blank_identifier() -> None:
    invalid = type(
        "InvalidRule",
        (BaseRule,),
        {
            "rule_id": " ",
            "check": AlphaRule.check,
        },
    )

    registry = EngineRegistry()

    with pytest.raises(RegistryError, match="valid identifier"):
        registry._register_from_module(_module_with(invalid), BaseRule)


def test_registry_rejects_duplicate_rule_identifiers() -> None:
    duplicate = type(
        "DuplicateRule",
        (BaseRule,),
        {
            "rule_id": "alpha.rule",
            "check": AlphaRule.check,
        },
    )

    registry = EngineRegistry()
    registry._register_from_module(_module_with(AlphaRule), BaseRule)

    with pytest.raises(RegistryError, match="Duplicate identifier"):
        registry._register_from_module(_module_with(duplicate), BaseRule)


def test_registry_ignores_unrelated_and_imported_classes() -> None:
    module = ModuleType("tests.dynamic_registry_module")

    class Unrelated:
        pass

    imported_collector = type(
        "ImportedCollector",
        (BaseCollector,),
        {
            "__module__": "tests.some_other_module",
            "collector_id": "imported",
            "collect": AlphaCollector.collect,
        },
    )

    setattr(module, "Unrelated", Unrelated)
    setattr(module, "ImportedCollector", imported_collector)

    registry = EngineRegistry()
    registry._register_from_module(module, BaseCollector)

    assert registry.collector_ids == ()


def test_registry_discovers_real_packages() -> None:
    registry = EngineRegistry.discover()

    assert registry.collector_ids
    assert registry.rule_ids

    assert "entities" in registry.collector_ids
    assert "UNAVAILABLE_ENTITIES" in registry.rule_ids


def test_discover_package_ignores_module_without_package_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = ModuleType("tests.not_a_package")
    registry = EngineRegistry()

    monkeypatch.setattr(
        "custom_components.ha_inspector.engine.registry.import_module",
        lambda _name: module,
    )

    registry._discover_package("tests.not_a_package", BaseCollector)

    assert registry.collector_ids == ()

def test_registry_creates_disk_free_space_rule_with_defaults() -> None:
    """Registry instantiates configurable rules using default thresholds."""
    registry = EngineRegistry.discover()

    disk_rule = next(
        rule
        for rule in registry.create_rules()
        if rule.rule_id == "DISK_FREE_SPACE"
    )

    assert disk_rule.warning_threshold == 20.0
    assert disk_rule.error_threshold == 10.0


def test_registry_creates_rule_with_configuration() -> None:
    """Registry passes rule-specific configuration to its constructor."""
    registry = EngineRegistry.discover()

    disk_rule = next(
        rule
        for rule in registry.create_rules(
            {
                "DISK_FREE_SPACE": {
                    "warning_threshold": 30.0,
                    "error_threshold": 15.0,
                }
            }
        )
        if rule.rule_id == "DISK_FREE_SPACE"
    )

    assert disk_rule.warning_threshold == 30.0
    assert disk_rule.error_threshold == 15.0


def test_registry_rejects_unknown_rule_configuration() -> None:
    """Configuration cannot reference a rule that is not registered."""
    registry = EngineRegistry.discover()

    with pytest.raises(
        RegistryError,
        match="Configuration references unknown rules: UNKNOWN_RULE",
    ):
        registry.create_rules(
            {
                "UNKNOWN_RULE": {
                    "threshold": 1,
                }
            }
        )


def test_registry_creates_recorder_rules_with_defaults() -> None:
    """Registry preserves Recorder rule default thresholds."""
    registry = EngineRegistry.discover()
    rules = {
        rule.rule_id: rule
        for rule in registry.create_rules()
    }

    keep_days_rule = rules["RECORDER_KEEP_DAYS"]
    database_size_rule = rules["RECORDER_DATABASE_SIZE"]

    assert keep_days_rule.warning_threshold == 30
    assert keep_days_rule.error_threshold == 90
    assert database_size_rule.warning_threshold_bytes == 5 * 1024**3
    assert database_size_rule.error_threshold_bytes == 10 * 1024**3


def test_registry_creates_recorder_rules_with_configuration() -> None:
    """Registry passes Recorder-specific threshold configuration."""
    registry = EngineRegistry.discover()
    rules = {
        rule.rule_id: rule
        for rule in registry.create_rules(
            {
                "RECORDER_KEEP_DAYS": {
                    "warning_threshold": 45,
                    "error_threshold": 120,
                },
                "RECORDER_DATABASE_SIZE": {
                    "warning_threshold_bytes": 8 * 1024**3,
                    "error_threshold_bytes": 16 * 1024**3,
                },
            }
        )
    }

    keep_days_rule = rules["RECORDER_KEEP_DAYS"]
    database_size_rule = rules["RECORDER_DATABASE_SIZE"]

    assert keep_days_rule.warning_threshold == 45
    assert keep_days_rule.error_threshold == 120
    assert database_size_rule.warning_threshold_bytes == 8 * 1024**3
    assert database_size_rule.error_threshold_bytes == 16 * 1024**3
