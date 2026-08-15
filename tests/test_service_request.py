from __future__ import annotations

import pytest

from custom_components.ha_inspector import (
    _build_request,
    _profile_definition,
)
from custom_components.ha_inspector.engine.profiles import (
    InspectionProfileError,
)


def test_build_request_without_profile():
    request = _build_request(
        {
            "include_rule_ids": [
                "CORE_VERSION",
            ],
            "diagnostics": True,
        }
    )

    assert request.include_rule_ids == (
        "CORE_VERSION",
    )
    assert request.diagnostics is True


def test_build_request_with_short_profile():
    request = _build_request(
        {
            "profile": "quick",
        }
    )

    assert "CORE_VERSION" in request.include_rule_ids
    assert "UNAVAILABLE_ENTITIES" in request.include_rule_ids
    assert request.diagnostics is False


def test_build_request_with_profile_mapping():
    request = _build_request(
        {
            "profile": {
                "id": "entities",
            },
        }
    )

    assert request.include_rule_ids == (
        "DUPLICATE_ENTITY_NAMES",
        "UNAVAILABLE_ENTITIES",
        "UNKNOWN_ENTITIES",
    )


def test_explicit_fields_override_profile():
    request = _build_request(
        {
            "profile": "quick",
            "include_rule_ids": [
                "RECORDER_AVAILABILITY",
            ],
        }
    )

    assert request.include_rule_ids == (
        "RECORDER_AVAILABILITY",
    )


def test_explicit_diagnostics_overrides_profile():
    request = _build_request(
        {
            "profile": "quick",
            "diagnostics": True,
        }
    )

    assert request.diagnostics is True


def test_profile_mapping_supports_overrides():
    request = _build_request(
        {
            "profile": {
                "id": "quick",
                "overrides": {
                    "exclude_rule_ids": [
                        "UNAVAILABLE_ENTITIES",
                    ],
                    "diagnostics": True,
                },
            },
        }
    )

    assert request.exclude_rule_ids == (
        "UNAVAILABLE_ENTITIES",
    )
    assert request.diagnostics is True


def test_explicit_fields_override_profile_overrides():
    request = _build_request(
        {
            "profile": {
                "id": "quick",
                "overrides": {
                    "diagnostics": True,
                },
            },
            "diagnostics": False,
        }
    )

    assert request.diagnostics is False


def test_profile_string_is_normalized():
    profile_id, overrides = _profile_definition(
        " QUICK "
    )

    assert profile_id == "QUICK"
    assert overrides == {}


def test_profile_mapping_requires_id():
    with pytest.raises(
        InspectionProfileError,
        match="must contain a non-empty 'id'",
    ):
        _build_request(
            {
                "profile": {},
            }
        )


def test_profile_rejects_invalid_type():
    with pytest.raises(
        InspectionProfileError,
        match="must be a string or mapping",
    ):
        _build_request(
            {
                "profile": 123,
            }
        )


def test_profile_rejects_unknown_options():
    with pytest.raises(
        InspectionProfileError,
        match="Unknown inspection profile options",
    ):
        _build_request(
            {
                "profile": {
                    "id": "quick",
                    "unexpected": True,
                },
            }
        )


def test_profile_rejects_unknown_overrides():
    with pytest.raises(
        InspectionProfileError,
        match="Unknown inspection profile overrides",
    ):
        _build_request(
            {
                "profile": {
                    "id": "quick",
                    "overrides": {
                        "unexpected": True,
                    },
                },
            }
        )


def test_unknown_profile_is_rejected():
    with pytest.raises(
        InspectionProfileError,
        match="Unknown inspection profile",
    ):
        _build_request(
            {
                "profile": "missing",
            }
        )

def test_profile_rejects_empty_string() -> None:
    with pytest.raises(
        InspectionProfileError,
        match="identifier cannot be empty",
    ):
        _profile_definition("   ")


def test_profile_mapping_accepts_none_overrides() -> None:
    profile_id, overrides = _profile_definition(
        {
            "id": "quick",
            "overrides": None,
        }
    )

    assert profile_id == "quick"
    assert overrides == {}


def test_profile_rejects_non_mapping_overrides() -> None:
    with pytest.raises(
        InspectionProfileError,
        match="overrides must be a mapping",
    ):
        _profile_definition(
            {
                "id": "quick",
                "overrides": "invalid",
            }
        )