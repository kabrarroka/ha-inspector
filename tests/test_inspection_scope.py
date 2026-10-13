"""Tests for comparable inspection scopes."""

from __future__ import annotations

from custom_components.ha_inspector.engine.inspection_scope import (
    inspection_scope,
)
from custom_components.ha_inspector.engine.request import InspectionRequest


def test_default_requests_have_equal_scope() -> None:
    """Equivalent default inspections share a scope."""
    first = InspectionRequest()
    second = InspectionRequest()

    assert inspection_scope(first) == inspection_scope(second)


def test_filter_order_does_not_change_scope() -> None:
    """Normalized filter ordering does not affect comparability."""
    first = InspectionRequest(
        include_rule_ids=("RULE_B", "RULE_A"),
    )
    second = InspectionRequest(
        include_rule_ids=("RULE_A", "RULE_B"),
    )

    assert inspection_scope(first) == inspection_scope(second)


def test_different_filters_have_different_scope() -> None:
    """Different rule selections must not be compared."""
    first = InspectionRequest(
        include_categories=("entities",),
    )
    second = InspectionRequest(
        include_categories=("storage",),
    )

    assert inspection_scope(first) != inspection_scope(second)


def test_language_does_not_change_scope() -> None:
    """Presentation language does not affect selected rules."""
    first = InspectionRequest(language="es")
    second = InspectionRequest(language="en")

    assert inspection_scope(first) == inspection_scope(second)


def test_diagnostics_does_not_change_scope() -> None:
    """Diagnostic output does not affect selected rules."""
    first = InspectionRequest(diagnostics=True)
    second = InspectionRequest(diagnostics=False)

    assert inspection_scope(first) == inspection_scope(second)


def test_scope_is_stable_and_serializable() -> None:
    """Inspection scope is a deterministic string."""
    request = InspectionRequest(
        include_rule_ids=("RULE_A",),
        exclude_tags=("experimental",),
    )

    scope = inspection_scope(request)

    assert isinstance(scope, str)
    assert scope
    assert scope == inspection_scope(request)
