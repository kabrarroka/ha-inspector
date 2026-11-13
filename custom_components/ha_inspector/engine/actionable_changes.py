"""Classify and prioritize finding changes between inspections."""

from __future__ import annotations

from typing import Literal, TypedDict

from .finding_deltas import FindingDeltas

type ChangeType = Literal[
    "new",
    "worsened",
    "improved",
    "resolved",
]

type ChangePriority = Literal[
    "critical",
    "high",
    "medium",
    "low",
    "none",
]


class ActionableChange(TypedDict):
    """Represent one classified inspection finding change."""

    id: str
    change_type: ChangeType
    severity: str
    priority: ChangePriority
    requires_action: bool


_PRIORITY_BY_SEVERITY: dict[str, ChangePriority] = {
    "critical": "critical",
    "error": "high",
    "warning": "medium",
    "info": "low",
}

_PRIORITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "none": 4,
}

_CHANGE_ORDER = {
    "new": 0,
    "worsened": 1,
    "improved": 2,
    "resolved": 3,
}


def classify_actionable_changes(
    deltas: FindingDeltas | None,
) -> tuple[ActionableChange, ...]:
    """Classify finding changes and order them by priority."""
    if deltas is None:
        return ()

    changes: list[ActionableChange] = []

    for finding in deltas.added:
        severity = finding["severity"]
        changes.append(
            {
                "id": finding["id"],
                "change_type": "new",
                "severity": severity,
                "priority": _PRIORITY_BY_SEVERITY[severity],
                "requires_action": True,
            }
        )

    for finding in deltas.severity_changed:
        worsened = finding["direction"] == "worsened"
        severity = finding["current_severity"]

        changes.append(
            {
                "id": finding["id"],
                "change_type": "worsened" if worsened else "improved",
                "severity": severity,
                "priority": (
                    _PRIORITY_BY_SEVERITY[severity]
                    if worsened
                    else "none"
                ),
                "requires_action": worsened,
            }
        )

    for finding in deltas.resolved:
        changes.append(
            {
                "id": finding["id"],
                "change_type": "resolved",
                "severity": finding["severity"],
                "priority": "none",
                "requires_action": False,
            }
        )

    return tuple(
        sorted(
            changes,
            key=lambda change: (
                _PRIORITY_ORDER[change["priority"]],
                _CHANGE_ORDER[change["change_type"]],
                change["id"],
            ),
        )
    )


__all__ = [
    "ActionableChange",
    "ChangePriority",
    "ChangeType",
    "classify_actionable_changes",
]
