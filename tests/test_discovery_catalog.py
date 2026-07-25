"""Tests for automatic discovery, registry and catalog."""

from __future__ import annotations

import pytest

from custom_components.ha_inspector.engine.catalog import RuleCatalog
from custom_components.ha_inspector.engine.models import Finding
from custom_components.ha_inspector.engine.registry import EngineRegistry, RegistryError
from custom_components.ha_inspector.engine.rules.base import BaseRule
from custom_components.ha_inspector.engine.severity import Severity


class AlphaRule(BaseRule):
    rule_id = "test.alpha"
    title = "Alpha"
    category = "system"
    severity = Severity.INFO
    weight = 1

    async def check(self, context) -> list[Finding]:
        return []


class BetaRule(BaseRule):
    rule_id = "test.beta"
    title = "Beta"
    category = "network"
    severity = Severity.WARNING
    weight = 2

    async def check(self, context) -> list[Finding]:
        return []


class DuplicateAlphaRule(BaseRule):
    rule_id = "test.alpha"
    title = "Duplicate"
    category = "system"
    severity = Severity.ERROR
    weight = 3

    async def check(self, context) -> list[Finding]:
        return []


def test_registry_registers_rules_in_deterministic_order() -> None:
    registry = EngineRegistry()
    registry.register_rule(BetaRule)
    registry.register_rule(AlphaRule)

    assert registry.rule_ids == ("test.alpha", "test.beta")
    assert [rule.rule_id for rule in registry.create_rules()] == [
        "test.alpha",
        "test.beta",
    ]


def test_registry_rejects_duplicate_identifiers() -> None:
    registry = EngineRegistry()
    registry.register_rule(AlphaRule)

    with pytest.raises(RegistryError, match="Duplicate identifier"):
        registry.register_rule(DuplicateAlphaRule)


def test_catalog_is_serializable_and_sorted() -> None:
    catalog = RuleCatalog([BetaRule(), AlphaRule()]).as_dict()

    assert catalog["total_rules"] == 2
    assert catalog["categories"] == ["network", "system"]
    assert [entry["id"] for entry in catalog["rules"]] == [
        "test.alpha",
        "test.beta",
    ]


def test_catalog_supports_legacy_rule_metadata() -> None:
    entry = RuleCatalog([AlphaRule()]).as_list()[0]

    assert entry["rule_id"] == "test.alpha"
    assert entry["severity"] == "info"
    assert entry["weight"] == 1
