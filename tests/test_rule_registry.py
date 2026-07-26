"""Tests for the read-only rule metadata registry."""

from __future__ import annotations

import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.models import Finding
from custom_components.ha_inspector.engine.rule_registry import (
    RuleRegistry,
    RuleRegistryEntry,
    RuleRegistryError,
)
from custom_components.ha_inspector.engine.rules.base import BaseRule
from custom_components.ha_inspector.engine.severity import Severity


class SystemAlphaRule(BaseRule):
    rule_id = "system.alpha"
    title = "System alpha"
    category = "system"
    severity = Severity.WARNING
    tags = ("core", "version")
    weight = 4
    recommendation = "Review alpha."

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        del context
        raise AssertionError("The registry must not execute rules")


class VersionBetaRule(BaseRule):
    rule_id = "versions.beta"
    title = "Version beta"
    category = "versions"
    severity = Severity.INFO
    tags = ("version",)
    weight = 1

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        del context
        raise AssertionError("The registry must not execute rules")


class DuplicateAlphaRule(SystemAlphaRule):
    rule_id = "system.alpha"


def make_registry() -> RuleRegistry:
    """Create a deterministic registry fixture."""
    return RuleRegistry(
        [
            VersionBetaRule(),
            SystemAlphaRule(),
        ]
    )


def test_registry_builds_metadata_without_executing_rules() -> None:
    registry = make_registry()

    assert len(registry) == 2
    assert registry.rule_ids == (
        "system.alpha",
        "versions.beta",
    )


def test_registry_iteration_is_deterministic() -> None:
    registry = make_registry()

    assert [
        entry.rule_id
        for entry in registry
    ] == [
        "system.alpha",
        "versions.beta",
    ]


def test_get_rule_returns_immutable_snapshot() -> None:
    registry = make_registry()

    entry = registry.get_rule("system.alpha")

    assert isinstance(entry, RuleRegistryEntry)
    assert entry.rule_id == "system.alpha"
    assert entry.title == "System alpha"
    assert entry.category == "system"
    assert entry.severity == "warning"
    assert entry.tags == ("core", "version")
    assert entry.weight == 4
    assert entry.recommendation == "Review alpha."


def test_get_rule_rejects_unknown_identifier() -> None:
    registry = make_registry()

    with pytest.raises(
        KeyError,
        match="Unknown rule identifier: missing.rule",
    ):
        registry.get_rule("missing.rule")


def test_registry_supports_membership() -> None:
    registry = make_registry()

    assert "system.alpha" in registry
    assert "missing.rule" not in registry


def test_list_rules_filters_by_category_and_tag() -> None:
    registry = make_registry()

    assert [
        entry.rule_id
        for entry in registry.list_rules(category="system")
    ] == ["system.alpha"]

    assert [
        entry.rule_id
        for entry in registry.list_rules(tag="version")
    ] == [
        "system.alpha",
        "versions.beta",
    ]

    assert registry.list_rules(
        category="versions",
        tag="core",
    ) == ()


def test_registry_lists_categories_and_tags() -> None:
    registry = make_registry()

    assert registry.categories() == ("system", "versions")
    assert registry.tags() == ("core", "version")


def test_as_dicts_returns_json_friendly_copies() -> None:
    registry = make_registry()

    exported = registry.as_dicts(category="system")
    exported[0]["tags"].append("mutated")

    assert exported == [
        {
            "id": "system.alpha",
            "rule_id": "system.alpha",
            "title": "System alpha",
            "category": "system",
            "severity": "warning",
            "tags": ["core", "version", "mutated"],
            "weight": 4,
            "recommendation": "Review alpha.",
        }
    ]
    assert registry.get_rule("system.alpha").tags == (
        "core",
        "version",
    )


def test_registry_rejects_duplicate_identifiers() -> None:
    with pytest.raises(
        RuleRegistryError,
        match="Duplicate rule identifier 'system.alpha'",
    ):
        RuleRegistry(
            [
                SystemAlphaRule(),
                DuplicateAlphaRule(),
            ]
        )


def test_empty_registry_is_supported() -> None:
    registry = RuleRegistry([])

    assert len(registry) == 0
    assert registry.rule_ids == ()
    assert registry.list_rules() == ()
    assert registry.categories() == ()
    assert registry.tags() == ()
    assert registry.as_dicts() == []
