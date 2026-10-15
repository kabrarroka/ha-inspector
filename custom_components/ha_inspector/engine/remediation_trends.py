"""Historical remediation lifecycle trend analytics."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise
from typing import Any

from .trends import TrendDirection

_REMEDIATION_FIELDS = (
    "pending",
    "in_progress",
    "resolved",
    "completed_actions",
    "remaining_actions",
    "new_references",
)


@dataclass(frozen=True, slots=True)
class RemediationLifecycleTrend:
    """Describe remediation lifecycle evolution across inspections."""

    direction: TrendDirection
    samples: int
    pending_delta: int | None
    in_progress_delta: int | None
    resolved_delta: int | None
    completed_actions_delta: int | None
    remaining_actions_delta: int | None
    new_references_delta: int | None
    regression_count: int
    remaining_actions_regression_count: int
    new_references_regression_count: int

    def as_dict(self) -> dict[str, int | str | None]:
        """Return a JSON-serializable trend summary."""
        return {
            "direction": self.direction,
            "samples": self.samples,
            "pending_delta": self.pending_delta,
            "in_progress_delta": self.in_progress_delta,
            "resolved_delta": self.resolved_delta,
            "completed_actions_delta": self.completed_actions_delta,
            "remaining_actions_delta": self.remaining_actions_delta,
            "new_references_delta": self.new_references_delta,
            "regression_count": self.regression_count,
            "remaining_actions_regression_count": (
                self.remaining_actions_regression_count
            ),
            "new_references_regression_count": (
                self.new_references_regression_count
            ),
        }


def _remediation_values(
    entry: dict[str, Any],
) -> dict[str, int] | None:
    """Extract valid remediation counters from one history entry."""
    remediation = entry.get("remediation")

    if not isinstance(remediation, dict):
        return None

    values: dict[str, int] = {}

    for field in _REMEDIATION_FIELDS:
        value = remediation.get(field)

        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            return None

        values[field] = value

    return values


def remediation_lifecycle_trend(
    entries: list[dict[str, Any]],
) -> RemediationLifecycleTrend:
    """Calculate remediation lifecycle trends from inspection history."""
    valid_entries: list[dict[str, int]] = []

    if entries:
        latest = entries[-1]
        reference_scope = latest.get("inspection_scope")
        latest_values = _remediation_values(latest)

        if (
            isinstance(reference_scope, str)
            and reference_scope.strip()
            and latest_values is not None
        ):
            valid_entries = [
                values
                for entry in entries
                if entry.get("inspection_scope") == reference_scope
                if (values := _remediation_values(entry)) is not None
            ]

    samples = len(valid_entries)

    remaining_regressions = 0
    reference_regressions = 0
    total_regressions = 0

    for previous, current in pairwise(valid_entries):
        remaining_increased = (
            current["remaining_actions"]
            > previous["remaining_actions"]
        )
        references_increased = (
            current["new_references"]
            > previous["new_references"]
        )

        if remaining_increased:
            remaining_regressions += 1

        if references_increased:
            reference_regressions += 1

        if remaining_increased or references_increased:
            total_regressions += 1

    deltas: dict[str, int | None] = {field: None for field in _REMEDIATION_FIELDS}

    if samples < 2:
        direction: TrendDirection = "insufficient_data"
    else:
        first = valid_entries[0]
        last = valid_entries[-1]

        deltas = {field: last[field] - first[field] for field in _REMEDIATION_FIELDS}

        remaining_delta = deltas["remaining_actions"]
        references_delta = deltas["new_references"]

        if (
            remaining_delta is not None
            and references_delta is not None
            and (remaining_delta > 0 or references_delta > 0)
        ):
            direction = "declining"
        elif remaining_delta is not None and remaining_delta < 0:
            direction = "improving"
        else:
            direction = "stable"

    return RemediationLifecycleTrend(
        direction=direction,
        samples=samples,
        pending_delta=deltas["pending"],
        in_progress_delta=deltas["in_progress"],
        resolved_delta=deltas["resolved"],
        completed_actions_delta=deltas["completed_actions"],
        remaining_actions_delta=deltas["remaining_actions"],
        new_references_delta=deltas["new_references"],
        regression_count=total_regressions,
        remaining_actions_regression_count=remaining_regressions,
        new_references_regression_count=reference_regressions,
    )


__all__ = [
    "RemediationLifecycleTrend",
    "remediation_lifecycle_trend",
]
