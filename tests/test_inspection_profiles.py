from __future__ import annotations

import pytest

from custom_components.ha_inspector.engine.profiles import (
    PROFILES,
    InspectionProfileError,
    create_profile_request,
    get_profile,
    list_profiles,
    normalize_profile_id,
)


def test_expected_profiles_are_registered():
    assert tuple(sorted(PROFILES)) == (
        "entities",
        "full",
        "integrations",
        "quick",
        "recorder",
        "storage",
        "system",
    )


def test_profile_ids_are_normalized():
    assert normalize_profile_id(" QUICK ") == "quick"
    assert get_profile(" QUICK ").profile_id == "quick"


def test_empty_profile_id_is_rejected():
    with pytest.raises(
        InspectionProfileError,
        match="cannot be empty",
    ):
        normalize_profile_id("   ")


def test_non_string_profile_id_is_rejected():
    with pytest.raises(
        InspectionProfileError,
        match="must be a string",
    ):
        normalize_profile_id(None)  # type: ignore[arg-type]


def test_unknown_profile_is_rejected():
    with pytest.raises(
        InspectionProfileError,
        match="Unknown inspection profile",
    ):
        get_profile("missing")


def test_full_profile_selects_all_rules():
    request = create_profile_request("full")

    assert request.include_rule_ids == ()
    assert request.include_categories == ()
    assert request.include_tags == ()
    assert request.exclude_rule_ids == ()


def test_quick_profile_selects_reduced_rule_set():
    request = create_profile_request("quick")

    assert request.include_rule_ids == (
        "CORE_VERSION",
        "INTEGRATION_SETUP_ERRORS",
        "OPERATING_SYSTEM_VERSION",
        "RECORDER_AVAILABILITY",
        "SUPERVISOR_AVAILABILITY",
        "SUPERVISOR_VERSION",
        "UNAVAILABLE_ENTITIES",
    )


def test_storage_profile_selects_disk_rule():
    request = create_profile_request("storage")

    assert request.include_rule_ids == ("DISK_FREE_SPACE",)


def test_diagnostics_can_be_overridden():
    request = create_profile_request(
        "quick",
        diagnostics=True,
    )

    assert request.diagnostics is True


def test_profile_requests_are_independent():
    first = create_profile_request(
        "quick",
        diagnostics=True,
    )
    second = create_profile_request("quick")

    assert first.diagnostics is True
    assert second.diagnostics is False


def test_list_profiles_is_deterministic():
    profiles = list_profiles()

    assert tuple(
        profile.profile_id
        for profile in profiles
    ) == tuple(sorted(PROFILES))


def test_profile_is_json_safe():
    profile_data = get_profile("entities").as_dict()

    assert profile_data["profile_id"] == "entities"
    assert profile_data["title"] == "Entity inspection"
    assert profile_data["request"]["include_rule_ids"] == [
        "DUPLICATE_ENTITY_NAMES",
        "UNAVAILABLE_ENTITIES",
        "UNKNOWN_ENTITIES",
    ]
