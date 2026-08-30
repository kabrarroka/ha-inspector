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
        "dependencies",
        "entities",
        "full",
        "integrations",
        "post_restore",
        "pre_upgrade",
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
        "BACKUP_AGE",
        "BACKUP_INTEGRITY",
        "DISK_FREE_SPACE",
        "INTEGRATION_SETUP_ERRORS",
        "RECORDER_AVAILABILITY",
        "SYSTEM_INFORMATION",
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
        "MISSING_ENTITY_REFERENCES",
        "UNAVAILABLE_ENTITIES",
        "UNKNOWN_ENTITIES",
        "UNREFERENCED_ENTITIES",
    ]


def test_profile_summary_can_be_localized() -> None:
    profile = get_profile("quick")

    data = profile.as_summary("es-ES")

    assert data["profile_id"] == "quick"
    assert data["title"] == "Inspección rápida"
    assert (
        data["description"]
        == "Ejecuta un conjunto reducido de comprobaciones "
        "importantes del sistema y de disponibilidad."
    )


def test_profile_dict_falls_back_to_english() -> None:
    profile = get_profile("system")

    data = profile.as_dict("fr")

    assert data["title"] == "System inspection"
    assert (
        data["description"]
        == "Inspect Home Assistant system and platform information."
    )



def test_all_profile_rule_ids_exist_in_registry() -> None:
    from custom_components.ha_inspector.engine.profiles import PROFILES
    from custom_components.ha_inspector.engine.registry import EngineRegistry

    registry = EngineRegistry.discover()
    known_rule_ids = set(registry.rule_ids)

    for profile in PROFILES.values():
        assert set(profile.request.include_rule_ids) <= known_rule_ids


def test_pre_upgrade_profile_selects_targeted_rules() -> None:
    """Pre-upgrade profile checks recovery and upgrade readiness."""
    request = create_profile_request("pre_upgrade")

    assert request.include_rule_ids == (
        "ADDON_HEALTH",
        "BACKUP_AGE",
        "BACKUP_AGENT_ERRORS",
        "BACKUP_COUNT",
        "BACKUP_INTEGRITY",
        "BACKUP_REDUNDANCY",
        "DISK_FREE_SPACE",
        "INTEGRATION_LIFECYCLE_ERRORS",
        "INTEGRATION_SETUP_ERRORS",
        "INTEGRATION_SETUP_RETRIES",
        "LOG_HEALTH",
        "NETWORK_CONNECTIVITY",
        "RECORDER_AVAILABILITY",
        "RECORDER_DATABASE_SIZE",
        "REPAIR_ISSUES",
        "SYSTEM_INFORMATION",
        "TIME_SYNCHRONIZATION",
    )


def test_post_restore_profile_selects_targeted_rules() -> None:
    """Post-restore profile checks restored system availability."""
    request = create_profile_request("post_restore")

    assert request.include_rule_ids == (
        "ADDON_HEALTH",
        "DISK_FREE_SPACE",
        "INTEGRATION_LIFECYCLE_ERRORS",
        "INTEGRATION_SETUP_ERRORS",
        "INTEGRATION_SETUP_RETRIES",
        "LOG_HEALTH",
        "NETWORK_CONNECTIVITY",
        "RECORDER_AVAILABILITY",
        "REPAIR_ISSUES",
        "SYSTEM_INFORMATION",
        "TIME_SYNCHRONIZATION",
        "UNAVAILABLE_ENTITIES",
        "UNKNOWN_ENTITIES",
    )


def test_targeted_profiles_are_localized() -> None:
    """Upgrade and restore profiles provide Spanish summaries."""
    pre_upgrade = get_profile("pre_upgrade").as_summary("es")
    post_restore = get_profile("post_restore").as_summary("es")

    assert pre_upgrade["title"] == "Inspección previa a actualización"
    assert (
        post_restore["title"]
        == "Inspección posterior a restauración"
    )

def test_entities_profile_includes_missing_entity_references() -> None:
    profile = get_profile("entities")

    assert "MISSING_ENTITY_REFERENCES" in profile.request.include_rule_ids


def test_entities_profile_includes_unreferenced_entities() -> None:
    profile = get_profile("entities")

    assert "UNREFERENCED_ENTITIES" in profile.request.include_rule_ids



def test_dependencies_profile_selects_dependency_rules() -> None:
    """Dependency profile selects dependency-oriented entity checks."""
    request = create_profile_request("dependencies")

    assert request.include_rule_ids == (
        "MISSING_ENTITY_REFERENCES",
        "UNAVAILABLE_ENTITIES",
        "UNKNOWN_ENTITIES",
        "UNREFERENCED_ENTITIES",
    )


def test_dependencies_profile_is_localized() -> None:
    """Dependency profile provides a Spanish summary."""
    profile = get_profile("dependencies").as_summary("es")

    assert profile["title"] == "Inspección de dependencias"
    assert (
        profile["description"]
        == "Inspecciona las dependencias de configuración, las "
        "referencias ausentes y las entidades referenciadas "
        "con problemas."
    )
