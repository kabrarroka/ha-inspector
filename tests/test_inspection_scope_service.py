"""Tests for effective inspection scope identity in service requests."""

from __future__ import annotations

from custom_components.ha_inspector import _build_request
from custom_components.ha_inspector.engine.inspection_scope import (
    inspection_scope,
)


def test_default_and_full_profile_have_equivalent_scopes() -> None:
    """Default and full inspections select the same effective rule scope."""
    default_request = _build_request({})
    full_request = _build_request({"profile": "full"})

    assert inspection_scope(default_request) == inspection_scope(full_request)


def test_equivalent_explicit_filters_have_equivalent_scopes() -> None:
    """Equivalent effective rule filters produce identical scope identities."""
    explicit_request = _build_request(
        {
            "include_categories": ["entities"],
        }
    )

    profile_request = _build_request(
        {
            "profile": "full",
            "include_categories": ["entities"],
        }
    )

    assert inspection_scope(explicit_request) == inspection_scope(profile_request)


def test_different_filters_produce_different_scopes() -> None:
    """Different rule selections must not share a scope."""
    entities_request = _build_request(
        {
            "include_categories": ["entities"],
        }
    )

    system_request = _build_request(
        {
            "include_categories": ["system"],
        }
    )

    assert inspection_scope(entities_request) != inspection_scope(system_request)


def test_diagnostics_option_does_not_change_scope() -> None:
    """Diagnostic output does not change the selected inspection rules."""
    standard_request = _build_request({})
    diagnostic_request = _build_request({"diagnostics": True})

    assert inspection_scope(standard_request) == inspection_scope(diagnostic_request)


def test_language_option_does_not_change_scope() -> None:
    """Output language does not change the selected inspection rules."""
    spanish_request = _build_request({"language": "es"})
    english_request = _build_request({"language": "en"})

    assert inspection_scope(spanish_request) == inspection_scope(english_request)
