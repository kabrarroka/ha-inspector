"""Tests for the inspection application service."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.inspection_service import (
    InspectionRequest,
    InspectionRequestError,
    InspectionService,
)
from custom_components.ha_inspector.engine.models import Finding
from custom_components.ha_inspector.engine.rule_profile import RuleProfile
from custom_components.ha_inspector.engine.rule_profiles import RuleProfiles
from custom_components.ha_inspector.engine.rule_selector import (
    RuleSelection,
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


class FakeEngine:
    def __init__(self) -> None:
        self.calls: list[tuple[object, object]] = []

    async def run_plan(self, context, plan):
        self.calls.append((context, plan))
        return {
            "context": context,
            "rule_ids": plan.rule_ids,
        }


def make_selector() -> RuleSelector:
    return RuleSelector(
        [
            SystemCoreRule(),
            SystemNetworkRule(),
            VersionFrontendRule(),
        ]
    )


def make_profiles() -> RuleProfiles:
    return RuleProfiles(
        [
            RuleProfile(
                name="quick",
                selection=RuleSelection(
                    include_categories={"system"},
                    exclude_tags={"network"},
                ),
            ),
            RuleProfile(
                name="full",
                selection=RuleSelection(),
            ),
        ]
    )


def test_request_defaults_to_all_rules() -> None:
    request = InspectionRequest()

    assert request.profile is None
    assert request.selection == RuleSelection()
    assert request.strict is True


def test_request_normalizes_values() -> None:
    request = InspectionRequest(
        profile=" quick ",
        strict=False,
    )

    assert request.profile == "quick"
    assert request.strict is False


def test_request_rejects_empty_profile() -> None:
    with pytest.raises(
        InspectionRequestError,
        match="profile must not be empty",
    ):
        InspectionRequest(profile=" ")


def test_profile_cannot_be_combined_with_direct_selection() -> None:
    with pytest.raises(
        InspectionRequestError,
        match=(
            "profile cannot be combined with direct selection criteria"
        ),
    ):
        InspectionRequest(
            profile="quick",
            categories={"system"},
        )


def test_request_is_immutable() -> None:
    request = InspectionRequest()

    with pytest.raises(FrozenInstanceError):
        request.strict = False  # type: ignore[misc]


def test_direct_selection_builds_plan() -> None:
    service = InspectionService(
        engine=FakeEngine(),
        selector=make_selector(),
    )

    plan = service.build_plan(
        InspectionRequest(
            categories={"system"},
            tags={"version", "network"},
            exclude_tags={"network"},
        )
    )

    assert plan.rule_ids == ("system.core",)


def test_profile_selection_builds_plan() -> None:
    service = InspectionService(
        engine=FakeEngine(),
        selector=make_selector(),
        profiles=make_profiles(),
    )

    plan = service.build_plan(
        InspectionRequest(profile="quick")
    )

    assert plan.rule_ids == ("system.core",)


def test_profile_requires_profile_registry() -> None:
    service = InspectionService(
        engine=FakeEngine(),
        selector=make_selector(),
    )

    with pytest.raises(
        InspectionRequestError,
        match="inspection profiles are not configured",
    ):
        service.build_plan(
            InspectionRequest(profile="quick")
        )


def test_strict_mode_is_forwarded() -> None:
    service = InspectionService(
        engine=FakeEngine(),
        selector=make_selector(),
    )

    plan = service.build_plan(
        InspectionRequest(
            tags={"missing"},
            strict=False,
        )
    )

    assert plan.is_empty


@pytest.mark.asyncio
async def test_run_delegates_plan_to_engine() -> None:
    engine = FakeEngine()
    service = InspectionService(
        engine=engine,
        selector=make_selector(),
    )
    context = object()

    result = await service.run(
        context,
        InspectionRequest(rule_ids={"system.network"}),
    )

    assert result == {
        "context": context,
        "rule_ids": ("system.network",),
    }
    assert len(engine.calls) == 1
    assert engine.calls[0][0] is context
    assert engine.calls[0][1].rule_ids == ("system.network",)


@pytest.mark.asyncio
async def test_run_without_request_executes_all_rules() -> None:
    engine = FakeEngine()
    service = InspectionService(
        engine=engine,
        selector=make_selector(),
    )

    result = await service.run(object())

    assert result["rule_ids"] == (
        "system.core",
        "system.network",
        "versions.frontend",
    )


def test_request_export_is_json_friendly_and_isolated() -> None:
    request = InspectionRequest(
        categories={"system"},
        exclude_tags={"experimental"},
    )

    exported = request.as_dict()
    selection = exported["selection"]
    assert isinstance(selection, dict)
    selection["categories"].append("mutated")

    assert request.selection.include_categories == frozenset({"system"})
