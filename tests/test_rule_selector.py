"""Tests for rule selection and execution plans."""

from __future__ import annotations

import pytest

from custom_components.ha_inspector.engine.rule_registry import RuleRegistry
from custom_components.ha_inspector.engine.rule_selector import (
    RuleExecutionPlan,
    RuleSelector,
)
from custom_components.ha_inspector.engine.rules.base import BaseRule
from custom_components.ha_inspector.engine.severity import Severity


class SystemVersionRule(BaseRule):
    """System version rule."""

    rule_id = "system.version"
    title = "System version"
    category = "system"
    severity = Severity.INFO
    tags = ("version", "core")
    weight = 10
    recommendation = None

    async def check(self, context):
        return []


class SystemStorageRule(BaseRule):
    """System storage rule."""

    rule_id = "system.storage"
    title = "System storage"
    category = "system"
    severity = Severity.WARNING
    tags = ("storage",)
    weight = 20
    recommendation = "Review available storage."

    async def check(self, context):
        return []


class FrontendVersionRule(BaseRule):
    """Frontend version rule."""

    rule_id = "frontend.version"
    title = "Frontend version"
    category = "frontend"
    severity = Severity.INFO
    tags = ("version", "experimental")
    weight = 5
    recommendation = None

    async def check(self, context):
        return []


@pytest.fixture
def selector() -> RuleSelector:
    """Return a selector with representative rules."""
    registry = RuleRegistry(
        [
            SystemVersionRule(),
            SystemStorageRule(),
            FrontendVersionRule(),
        ]
    )
    return RuleSelector(registry)


def test_select_without_filters_returns_all_rules(
    selector: RuleSelector,
) -> None:
    plan = selector.select()

    assert plan.rule_ids == (
        "frontend.version",
        "system.storage",
        "system.version",
    )


def test_select_by_rule_id(selector: RuleSelector) -> None:
    plan = selector.select(
        include_rule_ids={"system.version"},
    )

    assert plan.rule_ids == ("system.version",)


def test_select_accepts_single_string_rule_id(
    selector: RuleSelector,
) -> None:
    plan = selector.select(
        include_rule_ids="system.version",
    )

    assert plan.rule_ids == ("system.version",)


def test_select_by_category(selector: RuleSelector) -> None:
    plan = selector.select(
        include_categories={"system"},
    )

    assert plan.rule_ids == (
        "system.storage",
        "system.version",
    )


def test_select_by_tag(selector: RuleSelector) -> None:
    plan = selector.select(
        include_tags={"version"},
    )

    assert plan.rule_ids == (
        "frontend.version",
        "system.version",
    )


def test_multiple_values_in_same_group_use_or_semantics(
    selector: RuleSelector,
) -> None:
    plan = selector.select(
        include_categories={"system", "frontend"},
    )

    assert plan.rule_ids == (
        "frontend.version",
        "system.storage",
        "system.version",
    )


def test_inclusion_groups_use_and_semantics(
    selector: RuleSelector,
) -> None:
    plan = selector.select(
        include_categories={"system"},
        include_tags={"version"},
    )

    assert plan.rule_ids == ("system.version",)


def test_exclude_by_rule_id(selector: RuleSelector) -> None:
    plan = selector.select(
        exclude_rule_ids={"system.storage"},
    )

    assert plan.rule_ids == (
        "frontend.version",
        "system.version",
    )


def test_exclude_by_category(selector: RuleSelector) -> None:
    plan = selector.select(
        exclude_categories={"frontend"},
    )

    assert plan.rule_ids == (
        "system.storage",
        "system.version",
    )


def test_exclude_by_tag(selector: RuleSelector) -> None:
    plan = selector.select(
        exclude_tags={"experimental"},
    )

    assert plan.rule_ids == (
        "system.storage",
        "system.version",
    )


def test_exclusions_use_or_semantics(
    selector: RuleSelector,
) -> None:
    plan = selector.select(
        exclude_rule_ids={"system.storage"},
        exclude_tags={"experimental"},
    )

    assert plan.rule_ids == ("system.version",)


def test_exclusions_are_applied_after_inclusions(
    selector: RuleSelector,
) -> None:
    plan = selector.select(
        include_tags={"version"},
        exclude_categories={"frontend"},
    )

    assert plan.rule_ids == ("system.version",)


def test_unknown_included_rule_id_raises_key_error(
    selector: RuleSelector,
) -> None:
    with pytest.raises(KeyError):
        selector.select(
            include_rule_ids={"unknown.rule"},
        )


def test_unknown_excluded_rule_id_raises_key_error(
    selector: RuleSelector,
) -> None:
    with pytest.raises(KeyError):
        selector.select(
            exclude_rule_ids={"unknown.rule"},
        )


def test_empty_filter_values_are_ignored(
    selector: RuleSelector,
) -> None:
    plan = selector.select(
        include_categories={"", "   "},
        include_tags={""},
    )

    assert plan.rule_ids == (
        "frontend.version",
        "system.storage",
        "system.version",
    )


def test_execution_plan_removes_duplicates_and_sorts() -> None:
    plan = RuleExecutionPlan(
        (
            "system.version",
            "frontend.version",
            "system.version",
        )
    )

    assert plan.rule_ids == (
        "frontend.version",
        "system.version",
    )


def test_execution_plan_supports_iteration_and_membership() -> None:
    plan = RuleExecutionPlan(
        (
            "system.storage",
            "system.version",
        )
    )

    assert tuple(plan) == (
        "system.storage",
        "system.version",
    )
    assert len(plan) == 2
    assert "system.storage" in plan
    assert "frontend.version" not in plan


def test_execution_plan_exports_json_safe_dictionary() -> None:
    plan = RuleExecutionPlan(
        (
            "system.version",
            "frontend.version",
        )
    )

    exported = plan.as_dict()

    assert exported == {
        "rule_ids": [
            "frontend.version",
            "system.version",
        ]
    }

    exported["rule_ids"].append("mutated.rule")

    assert plan.rule_ids == (
        "frontend.version",
        "system.version",
    )


def test_empty_execution_plan_is_valid() -> None:
    plan = RuleExecutionPlan(())

    assert len(plan) == 0
    assert tuple(plan) == ()
    assert plan.as_dict() == {"rule_ids": []}


def test_filters_can_produce_empty_plan(
    selector: RuleSelector,
) -> None:
    plan = selector.select(
        include_categories={"system"},
        include_tags={"experimental"},
    )

    assert plan.rule_ids == ()
