"""Stalled remediation detection helpers for HA Inspector."""

from __future__ import annotations

from math import isfinite
from typing import Final

DEFAULT_STALLED_THRESHOLD_SECONDS: Final = 7 * 24 * 60 * 60

_ACTIVE_REMEDIATION_STATUSES: Final = frozenset(
    {
        "pending",
        "in_progress",
    }
)


def is_remediation_stalled(
    status: str,
    age_seconds: float | None,
    *,
    threshold_seconds: float = DEFAULT_STALLED_THRESHOLD_SECONDS,
) -> bool:
    """Return whether remediation work has reached the stalled threshold."""
    if isinstance(threshold_seconds, bool):
        raise ValueError(
            "Stalled remediation threshold must be a finite non-negative number"
        )

    threshold = float(threshold_seconds)

    if not isfinite(threshold) or threshold < 0:
        raise ValueError(
            "Stalled remediation threshold must be a finite non-negative number"
        )

    if status not in _ACTIVE_REMEDIATION_STATUSES or age_seconds is None:
        return False

    if isinstance(age_seconds, bool):
        return False

    age = float(age_seconds)

    if not isfinite(age) or age < 0:
        return False

    return age >= threshold


__all__ = [
    "DEFAULT_STALLED_THRESHOLD_SECONDS",
    "is_remediation_stalled",
]
