"""Tests for stalled remediation detection."""

from __future__ import annotations

import math

import pytest

from custom_components.ha_inspector.engine.remediation_stalled import (
    DEFAULT_STALLED_THRESHOLD_SECONDS,
    is_remediation_stalled,
)


def test_default_stalled_threshold_is_seven_days() -> None:
    """Default stalled threshold is seven days."""
    assert DEFAULT_STALLED_THRESHOLD_SECONDS == 604800


@pytest.mark.parametrize("status", ["pending", "in_progress"])
def test_active_remediation_is_not_stalled_below_threshold(
    status: str,
) -> None:
    """Active remediation below the age threshold is not stalled."""
    assert not is_remediation_stalled(
        status,
        DEFAULT_STALLED_THRESHOLD_SECONDS - 1,
    )


@pytest.mark.parametrize("status", ["pending", "in_progress"])
def test_active_remediation_is_stalled_at_threshold(status: str) -> None:
    """Active remediation becomes stalled exactly at the threshold."""
    assert is_remediation_stalled(
        status,
        DEFAULT_STALLED_THRESHOLD_SECONDS,
    )


@pytest.mark.parametrize("status", ["pending", "in_progress"])
def test_active_remediation_is_stalled_above_threshold(status: str) -> None:
    """Active remediation above the age threshold is stalled."""
    assert is_remediation_stalled(
        status,
        DEFAULT_STALLED_THRESHOLD_SECONDS + 1,
    )


def test_resolved_remediation_is_never_stalled() -> None:
    """Resolved remediation is never considered stalled."""
    assert not is_remediation_stalled(
        "resolved",
        DEFAULT_STALLED_THRESHOLD_SECONDS * 2,
    )


def test_unknown_status_is_not_stalled() -> None:
    """Unknown remediation states are not considered stalled."""
    assert not is_remediation_stalled(
        "unknown",
        DEFAULT_STALLED_THRESHOLD_SECONDS * 2,
    )


def test_missing_age_is_not_stalled() -> None:
    """Remediation without known age cannot be considered stalled."""
    assert not is_remediation_stalled("pending", None)


@pytest.mark.parametrize(
    "age_seconds",
    [
        -1.0,
        math.nan,
        math.inf,
        -math.inf,
        True,
    ],
)
def test_invalid_age_is_not_stalled(age_seconds: float) -> None:
    """Invalid remediation ages do not produce stalled state."""
    assert not is_remediation_stalled(
        "pending",
        age_seconds,
        threshold_seconds=0,
    )


def test_custom_threshold_controls_stalled_detection() -> None:
    """A custom threshold controls stalled remediation detection."""
    assert not is_remediation_stalled(
        "pending",
        99,
        threshold_seconds=100,
    )
    assert is_remediation_stalled(
        "pending",
        100,
        threshold_seconds=100,
    )


@pytest.mark.parametrize(
    "threshold_seconds",
    [
        -1.0,
        math.nan,
        math.inf,
        -math.inf,
        True,
    ],
)
def test_invalid_threshold_is_rejected(threshold_seconds: float) -> None:
    """Invalid stalled thresholds are rejected."""
    with pytest.raises(
        ValueError,
        match="Stalled remediation threshold",
    ):
        is_remediation_stalled(
            "pending",
            100,
            threshold_seconds=threshold_seconds,
        )
