"""Tests for actionable finding change classification."""

from custom_components.ha_inspector.engine.actionable_changes import (
    classify_actionable_changes,
)
from custom_components.ha_inspector.engine.finding_deltas import FindingDeltas


def make_deltas(
    *,
    added=(),
    resolved=(),
    persistent=(),
    severity_changed=(),
):
    """Build finding deltas for classification tests."""
    return FindingDeltas(
        added=added,
        resolved=resolved,
        persistent=persistent,
        severity_changed=severity_changed,
    )


def test_none_returns_empty_result():
    assert classify_actionable_changes(None) == ()


def test_empty_deltas_returns_empty_result():
    assert classify_actionable_changes(make_deltas()) == ()


def test_new_findings_are_prioritized_by_severity():
    deltas = make_deltas(
        added=(
            {"id": "info", "severity": "info"},
            {"id": "warning", "severity": "warning"},
            {"id": "critical", "severity": "critical"},
            {"id": "error", "severity": "error"},
        )
    )

    changes = classify_actionable_changes(deltas)

    assert [item["id"] for item in changes] == [
        "critical",
        "error",
        "warning",
        "info",
    ]
    assert [item["priority"] for item in changes] == [
        "critical",
        "high",
        "medium",
        "low",
    ]
    assert all(item["change_type"] == "new" for item in changes)
    assert all(item["requires_action"] for item in changes)


def test_worsened_finding_requires_action():
    deltas = make_deltas(
        severity_changed=(
            {
                "id": "sensor.problem",
                "previous_severity": "warning",
                "current_severity": "error",
                "direction": "worsened",
            },
        )
    )

    changes = classify_actionable_changes(deltas)

    assert len(changes) == 1
    assert changes[0] == {
        "id": "sensor.problem",
        "change_type": "worsened",
        "severity": "error",
        "priority": "high",
        "requires_action": True,
    }


def test_improved_finding_does_not_require_action():
    deltas = make_deltas(
        severity_changed=(
            {
                "id": "sensor.improved",
                "previous_severity": "critical",
                "current_severity": "warning",
                "direction": "improved",
            },
        )
    )

    changes = classify_actionable_changes(deltas)

    assert changes == (
        {
            "id": "sensor.improved",
            "change_type": "improved",
            "severity": "warning",
            "priority": "none",
            "requires_action": False,
        },
    )


def test_resolved_finding_does_not_require_action():
    deltas = make_deltas(
        resolved=({"id": "sensor.resolved", "severity": "error"},)
    )

    changes = classify_actionable_changes(deltas)

    assert changes[0]["change_type"] == "resolved"
    assert changes[0]["priority"] == "none"
    assert changes[0]["requires_action"] is False


def test_unchanged_persistent_findings_are_ignored():
    deltas = make_deltas(
        persistent=({"id": "sensor.existing", "severity": "critical"},)
    )

    assert classify_actionable_changes(deltas) == ()


def test_severity_change_is_not_duplicated_by_persistent_finding():
    deltas = make_deltas(
        persistent=({"id": "sensor.changed", "severity": "error"},),
        severity_changed=(
            {
                "id": "sensor.changed",
                "previous_severity": "warning",
                "current_severity": "error",
                "direction": "worsened",
            },
        ),
    )

    changes = classify_actionable_changes(deltas)

    assert len(changes) == 1
    assert changes[0]["change_type"] == "worsened"


def test_order_is_deterministic():
    deltas = make_deltas(
        added=(
            {"id": "z", "severity": "error"},
            {"id": "a", "severity": "error"},
        ),
        resolved=({"id": "resolved", "severity": "critical"},),
        severity_changed=(
            {
                "id": "worsened",
                "previous_severity": "warning",
                "current_severity": "error",
                "direction": "worsened",
            },
            {
                "id": "improved",
                "previous_severity": "error",
                "current_severity": "warning",
                "direction": "improved",
            },
        ),
    )

    changes = classify_actionable_changes(deltas)

    assert [item["id"] for item in changes] == [
        "a",
        "z",
        "worsened",
        "improved",
        "resolved",
    ]
