"""Tests for remediation urgency classification."""

from __future__ import annotations

import math

import pytest

from custom_components.ha_inspector.engine.remediation_plans import (
    RemediationProgress,
)
from custom_components.ha_inspector.engine.remediation_stalled import (
    DEFAULT_STALLED_THRESHOLD_SECONDS,
)
from custom_components.ha_inspector.engine.remediation_urgency import (
    classify_remediation_urgency,
)


def make_progress(
    status: str,
    *,
    new_reference_count: int = 0,
) -> RemediationProgress:
    """Build remediation progress for urgency tests."""
    return RemediationProgress(
        entity_id="sensor.example",
        status=status,
        total_action_count=2,
        completed_action_count=0,
        remaining_action_count=2,
        new_reference_count=new_reference_count,
    )


@pytest.mark.parametrize("status", ["pending", "in_progress"])
def test_active_remediation_below_threshold_is_low(status: str) -> None:
    """Active remediation below the stalled threshold has low urgency."""
    progress = make_progress(status)

    assert classify_remediation_urgency(
        progress,
        DEFAULT_STALLED_THRESHOLD_SECONDS - 1,
    ) == "low"


@pytest.mark.parametrize("status", ["pending", "in_progress"])
def test_stalled_remediation_without_new_references_is_medium(
    status: str,
) -> None:
    """Stalled remediation without new references has medium urgency."""
    progress = make_progress(status)

    assert classify_remediation_urgency(
        progress,
        DEFAULT_STALLED_THRESHOLD_SECONDS,
    ) == "medium"


@pytest.mark.parametrize("status", ["pending", "in_progress"])
def test_stalled_remediation_with_new_references_is_high(
    status: str,
) -> None:
    """Stalled remediation with new references has high urgency."""
    progress = make_progress(status, new_reference_count=1)

    assert classify_remediation_urgency(
        progress,
        DEFAULT_STALLED_THRESHOLD_SECONDS,
    ) == "high"


def test_new_references_without_stalling_remain_low() -> None:
    """New references alone do not imply high urgency."""
    progress = make_progress("pending", new_reference_count=3)

    assert classify_remediation_urgency(progress, 10) == "low"


@pytest.mark.parametrize(
    "age_seconds",
    [None, -1.0, math.nan, math.inf, -math.inf, True],
)
def test_missing_or_invalid_age_is_low(age_seconds: float | None) -> None:
    """Unknown or invalid age cannot establish stalled urgency."""
    progress = make_progress("pending", new_reference_count=2)

    assert classify_remediation_urgency(progress, age_seconds) == "low"


def test_resolved_remediation_has_no_urgency() -> None:
    """Resolved remediation has no urgency."""
    progress = make_progress("resolved", new_reference_count=2)

    assert classify_remediation_urgency(
        progress,
        DEFAULT_STALLED_THRESHOLD_SECONDS * 2,
    ) == "none"


def test_unknown_status_has_no_urgency() -> None:
    """Unknown remediation status has no urgency."""
    progress = make_progress("unknown")

    assert classify_remediation_urgency(
        progress,
        DEFAULT_STALLED_THRESHOLD_SECONDS * 2,
    ) == "none"


def test_custom_threshold_controls_urgency() -> None:
    """Custom stalled thresholds also control urgency classification."""
    progress = make_progress("in_progress", new_reference_count=1)

    assert classify_remediation_urgency(
        progress,
        99,
        threshold_seconds=100,
    ) == "low"

    assert classify_remediation_urgency(
        progress,
        100,
        threshold_seconds=100,
    ) == "high"


@pytest.mark.parametrize(
    "threshold_seconds",
    [-1.0, math.nan, math.inf, -math.inf, True],
)
def test_invalid_threshold_is_rejected(threshold_seconds: float) -> None:
    """Invalid thresholds are rejected consistently."""
    progress = make_progress("pending")

    with pytest.raises(ValueError, match="Stalled remediation threshold"):
        classify_remediation_urgency(
            progress,
            100,
            threshold_seconds=threshold_seconds,
        )
