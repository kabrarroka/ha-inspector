"""Tests for the high-level rule selection API."""

from __future__ import annotations

import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.models import Finding
from custom_components.ha_inspector.engine.rule_selector import (
    RuleSelection,
    RuleSelectionError,
    RuleSelector,
)
from custom_components.ha_inspector.engine.rules.base import BaseRule


class SystemCoreRule(BaseRule):
    rule_id = "system.core"
    title = "System core"
    category = "system"
    tags = ("core", "version")

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        del context
        return []


class SystemNetworkRule(BaseRule):
    rule_id = "system.network"
    title = "System network"
    category = "system"
    tags = ("network",)

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        del context
        return []


class VersionFrontendRule(BaseRule):
    rule_id = "versions.frontend"
    title = "Frontend version"
    category = "versions"
    tags = ("version", "experimental")

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        del context
        return []


def make_selector() -> RuleSelector:
    return RuleSelector(
        [
            SystemCoreRule(),
            SystemNetworkRule(),
            VersionFrontendRule(),
        ]
    )


def test_selector_exposes_registry() -> None:
    selector = make_selector()

    assert selector.registry.rule_ids == (
        "system.core",
        "system.network",
        "versions.frontend",
    )


def test_empty_request_selects_all_rules_in_source_order() -> None:
    selector = make_selector()

    plan = selector.select()

    assert plan.rule_ids == (
        "system.core",
        "system.network",
        "versions.frontend",
    )


def test_selector_includes_rule_ids() -> None:
    selector = make_selector()

    plan = selector.select(
        include_rule_ids={
            "versions.frontend",
            "system.core",
        }
    )

    assert plan.rule_ids == (
        "system.core",
        "versions.frontend",
    )


def test_inclusion_dimensions_use_intersection() -> None:
    selector = make_selector()

    plan = selector.select(
        include_categories={"system"},
        include_tags={"version"},
    )

    assert plan.rule_ids == ("system.core",)


def test_values_within_one_dimension_use_union() -> None:
    selector = make_selector()

    plan = selector.select(
        include_tags={"network", "experimental"},
    )

    assert plan.rule_ids == (
        "system.network",
        "versions.frontend",
    )


def test_exclusions_take_precedence() -> None:
    selector = make_selector()

    plan = selector.select(
        include_categories={"system"},
        exclude_rule_ids={"system.core"},
    )

    assert plan.rule_ids == ("system.network",)


def test_exclusion_by_category_and_tag() -> None:
    selector = make_selector()

    by_category = selector.select(
        exclude_categories={"versions"},
    )
    by_tag = selector.select(
        exclude_tags={"experimental"},
    )

    assert by_category.rule_ids == (
        "system.core",
        "system.network",
    )
    assert by_tag.rule_ids == (
        "system.core",
        "system.network",
    )


def test_explicit_empty_inclusion_selects_no_rules() -> None:
    selector = make_selector()

    assert selector.select(
        include_rule_ids=[],
    ).is_empty
    assert selector.select(
        include_categories=[],
    ).is_empty
    assert selector.select(
        include_tags=[],
    ).is_empty


def test_strict_selection_rejects_unknown_values() -> None:
    selector = make_selector()

    with pytest.raises(
        RuleSelectionError,
        match="Unknown rule identifiers: 'missing.rule'",
    ):
        selector.select(include_rule_ids={"missing.rule"})

    with pytest.raises(
        RuleSelectionError,
        match="Unknown categories: 'missing'",
    ):
        selector.select(exclude_categories={"missing"})

    with pytest.raises(
        RuleSelectionError,
        match="Unknown tags: 'missing'",
    ):
        selector.select(include_tags={"missing"})


def test_non_strict_selection_ignores_unknown_values() -> None:
    selector = make_selector()

    plan = selector.select(
        include_rule_ids={
            "system.core",
            "missing.rule",
        },
        exclude_tags={"missing"},
        strict=False,
    )

    assert plan.rule_ids == ("system.core",)


def test_selection_is_immutable_and_normalized() -> None:
    selection = RuleSelection(
        include_rule_ids=[" system.core ", "system.core"],
        exclude_tags=[" experimental "],
    )

    assert selection.include_rule_ids == frozenset({"system.core"})
    assert selection.exclude_tags == frozenset({"experimental"})

    with pytest.raises(
        RuleSelectionError,
        match="include_tags must not contain empty values",
    ):
        RuleSelection(include_tags=[""])
