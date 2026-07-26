"""Tests for rule filtering in RuleEngine."""

from __future__ import annotations

import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.models import Finding
from custom_components.ha_inspector.engine.rule_engine import RuleEngine
from custom_components.ha_inspector.engine.rule_filter import RuleFilter
from custom_components.ha_inspector.engine.rules.base import BaseRule


class SystemAlphaRule(BaseRule):
    rule_id = "system.alpha"
    category = "system"

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        del context
        return []


class VersionBetaRule(BaseRule):
    rule_id = "versions.beta"
    category = "versions"

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        del context
        return []


class SystemGammaRule(BaseRule):
    rule_id = "system.gamma"
    category = "system"

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        del context
        return []


def make_engine() -> RuleEngine:
    """Create an engine with deterministic declaration order."""
    return RuleEngine(
        [
            SystemAlphaRule(),
            VersionBetaRule(),
            SystemGammaRule(),
        ]
    )


def test_filter_without_criteria_matches_every_rule() -> None:
    engine = make_engine()

    selected = engine.select_rules(RuleFilter())

    assert [rule.metadata.rule_id for rule in selected] == [
        "system.alpha",
        "versions.beta",
        "system.gamma",
    ]


def test_filter_selects_rule_ids_in_declaration_order() -> None:
    engine = make_engine()

    selected = engine.select_rules(
        RuleFilter(
            rule_ids={
                "system.gamma",
                "system.alpha",
            }
        )
    )

    assert [rule.metadata.rule_id for rule in selected] == [
        "system.alpha",
        "system.gamma",
    ]


def test_filter_selects_categories() -> None:
    engine = make_engine()

    selected = engine.select_rules(
        RuleFilter(categories={"system"})
    )

    assert [rule.metadata.rule_id for rule in selected] == [
        "system.alpha",
        "system.gamma",
    ]


def test_filter_combines_criteria_as_intersection() -> None:
    engine = make_engine()

    selected = engine.select_rules(
        RuleFilter(
            rule_ids={"system.alpha", "versions.beta"},
            categories={"system"},
        )
    )

    assert [rule.metadata.rule_id for rule in selected] == [
        "system.alpha",
    ]


def test_filter_supports_internal_predicate() -> None:
    engine = make_engine()

    selected = engine.select_rules(
        RuleFilter(
            predicate=lambda rule: rule.metadata.rule_id.endswith("gamma")
        )
    )

    assert [rule.metadata.rule_id for rule in selected] == [
        "system.gamma",
    ]


@pytest.mark.asyncio
async def test_engine_executes_only_selected_rules() -> None:
    engine = make_engine()

    executions = await engine.run(
        InspectionContext(),
        rule_filter=RuleFilter(categories={"versions"}),
    )

    assert [execution.rule_id for execution in executions] == [
        "versions.beta",
    ]

    execution = engine.execution_context
    assert execution is not None
    assert execution.total_rules == 1
    assert execution.rules_executed == 1
    assert execution.progress == 1.0


@pytest.mark.asyncio
async def test_explicit_empty_filter_executes_no_rules() -> None:
    engine = make_engine()

    executions = await engine.run(
        InspectionContext(),
        rule_filter=RuleFilter(rule_ids=[]),
    )

    assert executions == ()

    execution = engine.execution_context
    assert execution is not None
    assert execution.total_rules == 0
    assert execution.rules_executed == 0
    assert execution.progress == 1.0


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("rule_ids", {"rule_ids": [""]}),
        ("categories", {"categories": ["  "]}),
    ],
)
def test_filter_rejects_empty_values(
    field_name: str,
    kwargs: dict[str, list[str]],
) -> None:
    with pytest.raises(
        ValueError,
        match=rf"{field_name} must not contain empty values",
    ):
        RuleFilter(**kwargs)
