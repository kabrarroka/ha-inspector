"""Remediation urgency classification helpers for HA Inspector."""

from __future__ import annotations

from typing import Literal

from .remediation_plans import RemediationProgress
from .remediation_stalled import (
    DEFAULT_STALLED_THRESHOLD_SECONDS,
    is_remediation_stalled,
)

type RemediationUrgency = Literal[
    "none",
    "low",
    "medium",
    "high",
]


def classify_remediation_urgency(
    progress: RemediationProgress,
    age_seconds: float | None,
    *,
    threshold_seconds: float = DEFAULT_STALLED_THRESHOLD_SECONDS,
) -> RemediationUrgency:
    """Classify remediation urgency without modifying remediation state."""
    stalled = is_remediation_stalled(
        progress.status,
        age_seconds,
        threshold_seconds=threshold_seconds,
    )

    if progress.status == "resolved":
        return "none"

    if progress.status not in {"pending", "in_progress"}:
        return "none"

    if not stalled:
        return "low"

    if progress.new_reference_count > 0:
        return "high"

    return "medium"


__all__ = [
    "RemediationUrgency",
    "classify_remediation_urgency",
]
