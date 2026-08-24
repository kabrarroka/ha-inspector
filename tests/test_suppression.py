"""Tests for finding suppression policies."""

from custom_components.ha_inspector.engine.models import Finding
from custom_components.ha_inspector.engine.severity import Severity
from custom_components.ha_inspector.engine.suppression import (
    FindingSuppressionPolicy,
)


def _finding(finding_id: str) -> Finding:
    return Finding(
        finding_id=finding_id,
        severity=Severity.WARNING,
        title=finding_id,
        description="test",
    )


def test_empty_policy_suppresses_nothing() -> None:
    policy = FindingSuppressionPolicy()

    assert not policy.is_suppressed(_finding("A"))
    assert policy.finding_ids == frozenset()


def test_policy_normalizes_finding_ids() -> None:
    policy = FindingSuppressionPolicy(
        finding_ids=frozenset({" B ", "A", ""})
    )

    assert policy.finding_ids == frozenset({"A", "B"})


def test_partition_separates_active_and_suppressed_findings() -> None:
    policy = FindingSuppressionPolicy(
        finding_ids=frozenset({"B"})
    )

    active, suppressed = policy.partition(
        [_finding("A"), _finding("B"), _finding("C")]
    )

    assert [item.finding_id for item in active] == ["A", "C"]
    assert [item.finding_id for item in suppressed] == ["B"]


def test_policy_normalizes_none_finding_ids() -> None:
    """None normalizes to an empty suppression set."""
    policy = FindingSuppressionPolicy(finding_ids=None)  # type: ignore[arg-type]

    assert policy.finding_ids == frozenset()


def test_policy_normalizes_string_finding_id() -> None:
    """A single string is treated as one finding identifier."""
    policy = FindingSuppressionPolicy(
        finding_ids=" A "  # type: ignore[arg-type]
    )

    assert policy.finding_ids == frozenset({"A"})
