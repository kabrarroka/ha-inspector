"""Tests for the immutable rule metadata registry."""

from __future__ import annotations

import pytest

from custom_components.ha_inspector.engine.rule_registry import (
    RuleRegistry,
    RuleRegistryEntry,
    RuleRegistryError,
)
from custom_components.ha_inspector.engine.rules.base import BaseRule
from custom_components.ha_inspector.engine.severity import Severity


class ExampleRule(BaseRule):
    """Rule used to test registry metadata."""

    rule_id = "system.example"
    title = "Example rule"
    category = "system"
    severity = Severity.WARNING
    tags = ("example", "system")
    weight = 25
    recommendation = "Review the example configuration."

    def __init__(self) -> None:
        self.executed = False

    async def check(self, context):
        self.executed = True
        return []


class AnotherRule(BaseRule):
    """Second rule used for ordering and filtering."""

    rule_id = "frontend.version"
    title = "Frontend version"
    category = "frontend"
    severity = Severity.INFO
    tags = ("version",)
    weight = 10
    recommendation = None

    async def check(self, context):
        return []


class DuplicateRule(BaseRule):
    """Rule with a duplicated identifier."""

    rule_id = "system.example"
    title = "Duplicate rule"
    category = "system"
    severity = Severity.ERROR
    tags = ()

    async def check(self, context):
        return []


def test_registry_does_not_execute_rules() -> None:
    rule = ExampleRule()

    RuleRegistry([rule])

    assert rule.executed is False


def test_registry_orders_entries_by_rule_id() -> None:
    registry = RuleRegistry([ExampleRule(), AnotherRule()])

    assert tuple(entry.rule_id for entry in registry.list_rules()) == (
        "frontend.version",
        "system.example",
    )


def test_registry_entry_contains_complete_metadata() -> None:
    registry = RuleRegistry([ExampleRule()])

    entry = registry.get_rule("system.example")

    assert isinstance(entry, RuleRegistryEntry)
    assert entry.rule_id == "system.example"
    assert entry.title == "Example rule"
    assert entry.category == "system"
    assert entry.severity == "warning"
    assert entry.tags == ("example", "system")
    assert entry.weight == 25
    assert entry.recommendation == "Review the example configuration."


def test_unknown_rule_raises_key_error() -> None:
    registry = RuleRegistry([ExampleRule()])

    with pytest.raises(KeyError):
        registry.get_rule("unknown.rule")


def test_registry_membership_and_length() -> None:
    registry = RuleRegistry([ExampleRule(), AnotherRule()])

    assert len(registry) == 2
    assert "system.example" in registry
    assert "unknown.rule" not in registry


def test_registry_filters_by_category_and_tag() -> None:
    registry = RuleRegistry([ExampleRule(), AnotherRule()])

    assert tuple(
        entry.rule_id
        for entry in registry.list_rules(category="system")
    ) == ("system.example",)

    assert tuple(
        entry.rule_id
        for entry in registry.list_rules(tag="version")
    ) == ("frontend.version",)

    assert tuple(
        entry.rule_id
        for entry in registry.list_rules(
            category="system",
            tag="example",
        )
    ) == ("system.example",)

    assert registry.list_rules(
        category="frontend",
        tag="example",
    ) == ()


def test_registry_returns_sorted_categories_and_tags() -> None:
    registry = RuleRegistry([ExampleRule(), AnotherRule()])

    assert registry.categories() == ("frontend", "system")
    assert registry.tags() == ("example", "system", "version")


def test_exported_dicts_do_not_mutate_registry() -> None:
    registry = RuleRegistry([ExampleRule()])

    exported = registry.as_dicts()
    exported[0]["title"] = "Changed"
    exported[0]["tags"].append("mutated")

    entry = registry.get_rule("system.example")

    assert entry.title == "Example rule"
    assert entry.tags == ("example", "system")


def test_duplicate_rule_ids_raise_registry_error() -> None:
    with pytest.raises(
        RuleRegistryError,
        match="Duplicate rule identifier: system.example",
    ):
        RuleRegistry([ExampleRule(), DuplicateRule()])


def test_empty_registry_is_valid() -> None:
    registry = RuleRegistry([])

    assert len(registry) == 0
    assert registry.list_rules() == ()
    assert registry.categories() == ()
    assert registry.tags() == ()
    assert registry.as_dicts() == []
