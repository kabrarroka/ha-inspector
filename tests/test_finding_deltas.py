"""Tests for finding changes between inspections."""

from __future__ import annotations

from typing import Any

import pytest

from custom_components.ha_inspector.engine.finding_deltas import (
    compare_finding_deltas,
)


def _entry(
    findings: list[dict[str, str]],
) -> dict[str, Any]:
    """Build a comparable, complete inspection history entry."""
    return {
        "profile": "quick",
        "inspection_scope": "same-scope",
        "collectors_failed": 0,
        "findings": findings,
    }


def test_detects_added_resolved_persistent_and_severity_changes() -> None:
    """Identify finding lifecycle changes between two inspections."""
    previous = _entry([
        {"id": "RESOLVED", "severity": "warning"},
        {"id": "PERSISTENT", "severity": "info"},
        {"id": "WORSENED", "severity": "warning"},
        {"id": "IMPROVED", "severity": "critical"},
    ])
    current = _entry([
        {"id": "ADDED", "severity": "error"},
        {"id": "PERSISTENT", "severity": "info"},
        {"id": "WORSENED", "severity": "critical"},
        {"id": "IMPROVED", "severity": "warning"},
    ])

    comparison = compare_finding_deltas(previous, current)

    assert comparison is not None

    assert [item["id"] for item in comparison.added] == ["ADDED"]
    assert [item["id"] for item in comparison.resolved] == ["RESOLVED"]
    assert [item["id"] for item in comparison.persistent] == [
        "IMPROVED",
        "PERSISTENT",
        "WORSENED",
    ]

    assert comparison.severity_changed == (
        {
            "id": "IMPROVED",
            "previous_severity": "critical",
            "current_severity": "warning",
            "direction": "improved",
        },
        {
            "id": "WORSENED",
            "previous_severity": "warning",
            "current_severity": "critical",
            "direction": "worsened",
        },
    )





@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("profile", "full"),
        ("inspection_scope", "different-scope"),
        ("collectors_failed", 1),
        ("collectors_failed", None),
    ],
)
def test_rejects_incompatible_inspections(
    field: str,
    value: object,
) -> None:
    """Reject inspections with incompatible or incomplete metadata."""
    previous = _entry([{"id": "EXISTING", "severity": "warning"}])
    current = _entry([])

    current[field] = value

    assert compare_finding_deltas(previous, current) is None


@pytest.mark.parametrize(
    "field",
    [
        "profile",
        "inspection_scope",
        "collectors_failed",
        "findings",
    ],
)
def test_rejects_missing_previous_metadata(field: str) -> None:
    """Reject previous inspections without required comparison data."""
    previous = _entry([{"id": "EXISTING", "severity": "warning"}])
    current = _entry([])

    del previous[field]

    assert compare_finding_deltas(previous, current) is None


@pytest.mark.parametrize(
    "field",
    [
        "profile",
        "inspection_scope",
        "collectors_failed",
        "findings",
    ],
)
def test_rejects_missing_current_metadata(field: str) -> None:
    """Reject current inspections without required comparison data."""
    previous = _entry([{"id": "EXISTING", "severity": "warning"}])
    current = _entry([])

    del current[field]

    assert compare_finding_deltas(previous, current) is None



@pytest.mark.parametrize(
    "findings",
    [
        [{"id": "DUPLICATE", "severity": "warning"},
         {"id": "DUPLICATE", "severity": "error"}],
        [{"id": "", "severity": "warning"}],
        [{"id": 123, "severity": "warning"}],
        [{"id": "INVALID", "severity": "unknown"}],
        [{"id": "INVALID", "severity": 2}],
        [{"severity": "warning"}],
        [{"id": "INVALID"}],
        ["INVALID"],
        [None],
        {"id": "INVALID", "severity": "warning"},
        None,
    ],
)
@pytest.mark.parametrize("side", ["previous", "current"])
def test_rejects_invalid_findings(
    findings: object,
    side: str,
) -> None:
    """Reject malformed finding data on either side of a comparison."""
    previous = _entry([{"id": "EXISTING", "severity": "warning"}])
    current = _entry([])

    if side == "previous":
        previous["findings"] = findings
    else:
        current["findings"] = findings

    assert compare_finding_deltas(previous, current) is None



@pytest.mark.parametrize("side", ["previous", "current"])
def test_rejects_rule_execution_errors(side: str) -> None:
    """Do not compare inspections containing failed rule executions."""
    previous = _entry([
        {"id": "EXISTING", "severity": "warning"},
    ])
    current = _entry([])

    execution_error = {
        "id": "RULE_TEST.execution_error",
        "severity": "error",
    }

    if side == "previous":
        previous["findings"].append(execution_error)
    else:
        current["findings"].append(execution_error)

    assert compare_finding_deltas(previous, current) is None


def test_finding_deltas_as_dict() -> None:
    """Serialize finding changes into a JSON-compatible dictionary."""
    from custom_components.ha_inspector.engine.finding_deltas import FindingDeltas

    deltas = FindingDeltas(
        added=({"id": "NEW", "severity": "warning"},),
        resolved=({"id": "OLD", "severity": "error"},),
        persistent=({"id": "STABLE", "severity": "info"},),
        severity_changed=(
            {
                "id": "CHANGED",
                "previous_severity": "warning",
                "current_severity": "error",
                "direction": "worsened",
            },
        ),
    )

    assert deltas.as_dict() == {
        "added": [{"id": "NEW", "severity": "warning"}],
        "resolved": [{"id": "OLD", "severity": "error"}],
        "persistent": [{"id": "STABLE", "severity": "info"}],
        "severity_changed": [
            {
                "id": "CHANGED",
                "previous_severity": "warning",
                "current_severity": "error",
                "direction": "worsened",
            }
        ],
    }


def test_finding_deltas_rejects_invalid_comparison_metadata() -> None:
    """Reject ambiguous profiles and invalid collector failure counts."""
    from custom_components.ha_inspector.engine.finding_deltas import (
        compare_finding_deltas,
    )

    valid = {
        "profile": "quick",
        "inspection_scope": "same-scope",
        "collectors_failed": 0,
        "findings": [],
    }

    for invalid_profile in ("", False, 123):
        previous = {**valid, "profile": invalid_profile}
        current = {**valid, "profile": invalid_profile}

        assert compare_finding_deltas(previous, current) is None

    for invalid_count in (False, True, None, -1, "0", 0.0):
        previous = {**valid, "collectors_failed": invalid_count}

        assert compare_finding_deltas(previous, valid) is None
        assert compare_finding_deltas(valid, previous) is None



def test_finding_deltas_supports_matching_inspections_without_profile() -> None:
    """Compare matching unprofiled inspections without mixing profile modes."""
    from custom_components.ha_inspector.engine.finding_deltas import (
        compare_finding_deltas,
    )

    previous = {
        "profile": None,
        "inspection_scope": "same-scope",
        "collectors_failed": 0,
        "findings": [{"id": "OLD", "severity": "warning"}],
    }
    current = {
        "profile": None,
        "inspection_scope": "same-scope",
        "collectors_failed": 0,
        "findings": [{"id": "NEW", "severity": "warning"}],
    }

    deltas = compare_finding_deltas(previous, current)

    assert deltas is not None
    assert deltas.added == ({"id": "NEW", "severity": "warning"},)
    assert deltas.resolved == ({"id": "OLD", "severity": "warning"},)

    assert compare_finding_deltas(
        previous,
        {**current, "profile": "quick"},
    ) is None

    assert compare_finding_deltas(
        {**previous, "profile": "quick"},
        current,
    ) is None
