"""Tests for remediation lifecycle trends in inspection results."""

from __future__ import annotations

from custom_components.ha_inspector.engine.remediation_trends import (
    remediation_lifecycle_trend,
)
from custom_components.ha_inspector.engine.result import InspectionResult


def test_result_has_default_remediation_trend() -> None:
    """New inspection results have an insufficient-data trend."""
    result = InspectionResult()

    trend = result.remediation_trend

    assert trend.direction == "insufficient_data"
    assert trend.samples == 0
    assert trend.remaining_actions_delta is None


def test_result_serializes_default_remediation_trend() -> None:
    """Default remediation trends are included in serialized results."""
    result = InspectionResult()

    data = result.as_dict()

    assert data["remediation_trend"] == {
        "direction": "insufficient_data",
        "samples": 0,
        "pending_delta": None,
        "in_progress_delta": None,
        "resolved_delta": None,
        "completed_actions_delta": None,
        "remaining_actions_delta": None,
        "new_references_delta": None,
        "regression_count": 0,
        "remaining_actions_regression_count": 0,
        "new_references_regression_count": 0,
    }


def test_result_serializes_calculated_remediation_trend() -> None:
    """Calculated remediation trends are exposed in results."""
    result = InspectionResult()

    result.remediation_trend = remediation_lifecycle_trend(
        [
            {
                "profile": "full",
                "inspection_scope": "scope-full",
                "remediation": {
                    "pending": 2,
                    "in_progress": 0,
                    "resolved": 0,
                    "completed_actions": 0,
                    "remaining_actions": 4,
                    "new_references": 0,
                },
            },
            {
                "profile": "full",
                "inspection_scope": "scope-full",
                "remediation": {
                    "pending": 1,
                    "in_progress": 1,
                    "resolved": 1,
                    "completed_actions": 2,
                    "remaining_actions": 2,
                    "new_references": 0,
                },
            },
        ]
    )

    data = result.as_dict()

    assert data["remediation_trend"]["direction"] == "improving"
    assert data["remediation_trend"]["samples"] == 2
    assert data["remediation_trend"]["remaining_actions_delta"] == -2
    assert data["remediation_trend"]["completed_actions_delta"] == 2


def test_result_keeps_existing_remediation_lifecycle() -> None:
    """Adding trend analytics must preserve the lifecycle summary."""
    result = InspectionResult()

    data = result.as_dict()

    assert "remediation_lifecycle" in data
    assert "remediation_progress" in data
    assert "remediation_trend" in data
