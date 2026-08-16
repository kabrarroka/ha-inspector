"""Tests for HA Inspector engine capabilities."""

from types import ModuleType

from custom_components.ha_inspector.engine.capabilities import (
    CAPABILITIES_SCHEMA_VERSION,
    REQUEST_FILTERS,
    REQUEST_OPTIONS,
    EngineCapabilities,
    describe_engine,
)
from custom_components.ha_inspector.engine.collectors.base import BaseCollector
from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.models import Finding
from custom_components.ha_inspector.engine.registry import EngineRegistry
from custom_components.ha_inspector.engine.rules.base import BaseRule


class AlphaCollector(BaseCollector):
    collector_id = "alpha"

    async def collect(self, hass, context: InspectionContext) -> None:
        del hass, context


class AlphaRule(BaseRule):
    rule_id = "alpha.rule"
    title = "Alpha rule"
    category = "system"
    tags = ("alpha", "test")

    async def check(self, context: InspectionContext) -> list[Finding]:
        del context
        return []


def _module_with(*classes: type) -> ModuleType:
    module = ModuleType("tests.dynamic_capabilities_module")

    for candidate in classes:
        candidate.__module__ = module.__name__
        setattr(module, candidate.__name__, candidate)

    return module


def _registry() -> EngineRegistry:
    registry = EngineRegistry()

    registry._register_from_module(
        _module_with(AlphaCollector),
        BaseCollector,
    )
    registry._register_from_module(
        _module_with(AlphaRule),
        BaseRule,
    )

    return registry


def test_capabilities_are_built_from_registry() -> None:
    capabilities = EngineCapabilities.from_registry(_registry())

    assert capabilities.schema_version == CAPABILITIES_SCHEMA_VERSION
    assert capabilities.collectors == ("alpha",)
    assert capabilities.rule_ids == ("alpha.rule",)
    assert capabilities.categories == ("system",)
    assert capabilities.tags == ("alpha", "test")
    assert capabilities.request_filters == REQUEST_FILTERS
    assert capabilities.request_options == REQUEST_OPTIONS

    assert capabilities.rules == (
        {
            "rule_id": "alpha.rule",
            "title": "Alpha rule",
            "category": "system",
            "severity": "info",
            "tags": ["alpha", "test"],
            "weight": 0,
            "recommendation": None,
        },
    )


def test_capabilities_include_builtin_profiles() -> None:
    capabilities = EngineCapabilities.from_registry(_registry())

    assert capabilities.profile_ids == (
        "entities",
        "full",
        "integrations",
        "quick",
        "recorder",
        "storage",
        "system",
    )

    assert all(
        set(profile) == {
            "profile_id",
            "title",
            "description",
        }
        for profile in capabilities.profiles
    )


def test_capabilities_as_dict_returns_public_document() -> None:
    capabilities = EngineCapabilities.from_registry(_registry())

    data = capabilities.as_dict()

    assert data["schema_version"] == CAPABILITIES_SCHEMA_VERSION

    assert data["summary"] == {
        "collectors": 1,
        "rules": 1,
        "categories": 1,
        "tags": 2,
        "profiles": 7,
    }

    assert data["collectors"] == ["alpha"]
    assert data["rule_ids"] == ["alpha.rule"]
    assert data["categories"] == ["system"]
    assert data["tags"] == ["alpha", "test"]

    assert data["profile_ids"] == [
        "entities",
        "full",
        "integrations",
        "quick",
        "recorder",
        "storage",
        "system",
    ]

    assert data["request"]["filters"] == list(REQUEST_FILTERS)
    assert data["request"]["options"] == list(REQUEST_OPTIONS)

    assert data["request"]["defaults"] == {
        "include_rule_ids": [],
        "include_categories": [],
        "include_tags": [],
        "exclude_rule_ids": [],
        "exclude_categories": [],
        "exclude_tags": [],
        "diagnostics": False,
            "language": None,
    }


def test_describe_engine_returns_capability_document() -> None:
    data = describe_engine(_registry())

    assert data["schema_version"] == CAPABILITIES_SCHEMA_VERSION
    assert data["collectors"] == ["alpha"]
    assert data["rule_ids"] == ["alpha.rule"]
