"""Tests for reusable rule profiles."""

from __future__ import annotations

import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.models import Finding
from custom_components.ha_inspector.engine.rule_profile import (
    RuleProfile,
    RuleProfileError,
)
from custom_components.ha_inspector.engine.rule_profiles import RuleProfiles
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


def make_profiles() -> RuleProfiles:
    return RuleProfiles(
        [
            RuleProfile(
                name="network",
                title="Network",
                description="Network-related checks.",
                selection=RuleSelection(
                    include_tags={"network"},
                ),
            ),
            RuleProfile(
                name="quick",
                title="Quick",
                description="Fast system checks.",
                selection=RuleSelection(
                    include_categories={"system"},
                    exclude_tags={"network"},
                ),
            ),
            RuleProfile(
                name="full",
                title="Full",
                selection=RuleSelection(),
            ),
        ]
    )


def test_profile_normalizes_text() -> None:
    profile = RuleProfile(
        name=" quick ",
        title=" Quick checks ",
        description=" Fast diagnostics. ",
        selection=RuleSelection(),
    )

    assert profile.name == "quick"
    assert profile.title == "Quick checks"
    assert profile.description == "Fast diagnostics."


def test_profile_rejects_empty_text_fields() -> None:
    with pytest.raises(
        RuleProfileError,
        match="Profile name must not be empty",
    ):
        RuleProfile(
            name=" ",
            selection=RuleSelection(),
        )

    with pytest.raises(
        RuleProfileError,
        match="has an empty title",
    ):
        RuleProfile(
            name="quick",
            title=" ",
            selection=RuleSelection(),
        )

    with pytest.raises(
        RuleProfileError,
        match="has an empty description",
    ):
        RuleProfile(
            name="quick",
            description=" ",
            selection=RuleSelection(),
        )


def test_profile_is_immutable() -> None:
    profile = RuleProfile(
        name="quick",
        selection=RuleSelection(),
    )

    with pytest.raises(AttributeError):
        profile.name = "changed"  # type: ignore[misc]


def test_profiles_registry_is_deterministic() -> None:
    profiles = make_profiles()

    assert profiles.names == (
        "full",
        "network",
        "quick",
    )
    assert [
        profile.name
        for profile in profiles
    ] == [
        "full",
        "network",
        "quick",
    ]


def test_profiles_support_membership_and_lookup() -> None:
    profiles = make_profiles()

    assert "quick" in profiles
    assert "missing" not in profiles
    assert profiles.get("quick").title == "Quick"


def test_unknown_profile_raises_key_error() -> None:
    profiles = make_profiles()

    with pytest.raises(
        KeyError,
        match="Unknown rule profile: missing",
    ):
        profiles.get("missing")


def test_duplicate_profile_names_are_rejected() -> None:
    with pytest.raises(
        RuleProfileError,
        match="Duplicate profile name 'quick'",
    ):
        RuleProfiles(
            [
                RuleProfile(
                    name="quick",
                    selection=RuleSelection(),
                ),
                RuleProfile(
                    name=" quick ",
                    selection=RuleSelection(),
                ),
            ]
        )


def test_empty_profile_registry_is_supported() -> None:
    profiles = RuleProfiles([])

    assert len(profiles) == 0
    assert profiles.names == ()
    assert profiles.list_profiles() == ()
    assert profiles.as_dicts() == []


def test_profile_selects_execution_plan() -> None:
    profiles = make_profiles()
    selector = make_selector()

    assert profiles.select(
        "quick",
        selector,
    ).rule_ids == ("system.core",)

    assert profiles.select(
        "network",
        selector,
    ).rule_ids == ("system.network",)

    assert profiles.select(
        "full",
        selector,
    ).rule_ids == (
        "system.core",
        "system.network",
        "versions.frontend",
    )


def test_profile_preserves_strict_selector_validation() -> None:
    profiles = RuleProfiles(
        [
            RuleProfile(
                name="broken",
                selection=RuleSelection(
                    include_tags={"missing"},
                ),
            )
        ]
    )
    selector = make_selector()

    with pytest.raises(
        RuleSelectionError,
        match="Unknown tags: 'missing'",
    ):
        profiles.select("broken", selector)

    assert profiles.select(
        "broken",
        selector,
        strict=False,
    ).is_empty


def test_profile_export_is_json_friendly_and_isolated() -> None:
    profiles = make_profiles()

    exported = profiles.as_dicts()
    quick = next(
        item
        for item in exported
        if item["name"] == "quick"
    )
    selection = quick["selection"]
    assert isinstance(selection, dict)

    selection["exclude_tags"].append("mutated")

    original = profiles.get("quick")
    assert original.selection.exclude_tags == frozenset({"network"})
