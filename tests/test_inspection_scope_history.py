"""Tests for inspection scope persistence and compatibility."""

from __future__ import annotations

from custom_components.ha_inspector.engine.inspection_history import (
    InspectionHistory,
)


def test_history_entry_preserves_inspection_scope() -> None:
    """Compact history entries retain the inspection scope."""
    result = {
        "metadata": {
            "profile": "full",
            "inspection_scope": "scope-example",
        },
        "remediation_progress": {},
    }

    entry = InspectionHistory._build_entry(result)

    assert entry["inspection_scope"] == "scope-example"
    assert entry["profile"] == "full"


def test_history_entry_supports_legacy_results() -> None:
    """Results without inspection scope remain supported."""
    result = {
        "metadata": {
            "profile": "full",
        },
        "remediation_progress": {},
    }

    entry = InspectionHistory._build_entry(result)

    assert entry.get("inspection_scope") is None
    assert entry["profile"] == "full"


def test_current_history_entry_preserves_inspection_scope() -> None:
    """Temporary history entries retain the current inspection scope."""
    result = {
        "metadata": {
            "inspection_scope": "scope-current",
        },
        "remediation_progress": {
            "pending": 1,
            "in_progress": 0,
            "resolved": 0,
            "completed_actions": 0,
            "remaining_actions": 3,
            "new_references": 0,
        },
    }

    entry = InspectionHistory._build_entry(result)

    assert entry["inspection_scope"] == "scope-current"
    assert entry["remediation"]["remaining_actions"] == 3
