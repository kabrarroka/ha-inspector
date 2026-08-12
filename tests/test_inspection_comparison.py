"""Tests for inspection comparison."""

from custom_components.ha_inspector.engine.comparison import (
    CategoryComparison,
    FindingsComparison,
    InspectionComparison,
)
from custom_components.ha_inspector.engine.models import Finding
from custom_components.ha_inspector.engine.result import InspectionResult
from custom_components.ha_inspector.engine.score import HealthStatus
from custom_components.ha_inspector.engine.severity import Severity


def test_score_delta() -> None:
    previous = InspectionResult()
    current = InspectionResult()

    comparison = InspectionComparison(
        previous=previous,
        current=current,
    )

    assert comparison.score_delta == 0

def _finding(finding_id: str, severity: Severity) -> Finding:
    return Finding(
        finding_id=finding_id,
        severity=severity,
        title=finding_id,
        description="Test",
    )


def test_score_delta_when_score_improves() -> None:
    previous = InspectionResult()
    current = InspectionResult()

    previous.record_rule(
        category="system",
        weight=20,
        findings=[
            _finding("system.error", Severity.ERROR),
        ],
    )

    comparison = InspectionComparison(
        previous=previous,
        current=current,
    )

    assert previous.score == 86
    assert current.score == 100
    assert comparison.score_delta == 14

def test_health_delta_matches_score_delta() -> None:
    previous = InspectionResult()
    current = InspectionResult()

    previous.record_rule(
        category="system",
        weight=10,
        findings=[
            _finding("system.warning", Severity.WARNING),
        ],
    )

    comparison = InspectionComparison(
        previous=previous,
        current=current,
    )

    assert comparison.health_delta == comparison.score_delta

def test_category_comparison_properties() -> None:
    comparison = CategoryComparison(
        previous_score=80,
        current_score=92,
        previous_status=HealthStatus.GOOD,
        current_status=HealthStatus.EXCELLENT,
    )

    assert comparison.score_delta == 12
    assert comparison.improved
    assert not comparison.worsened
    assert not comparison.unchanged

    assert comparison.score_delta == 12

def test_findings_comparison_is_immutable() -> None:
    comparison = FindingsComparison(
        added=("new.warning",),
        removed=("old.warning",),
        unchanged=("persistent.warning",),
    )

    assert comparison.added == ("new.warning",)
    assert comparison.removed == ("old.warning",)
    assert comparison.unchanged == ("persistent.warning",)

def test_findings_comparison_contains_findings() -> None:
    added = _finding("added", Severity.WARNING)
    removed = _finding("removed", Severity.ERROR)
    unchanged = _finding("unchanged", Severity.INFO)

    comparison = FindingsComparison(
        added=(added,),
        removed=(removed,),
        unchanged=(unchanged,),
    )

    assert comparison.added[0] is added
    assert comparison.removed[0] is removed
    assert comparison.unchanged[0] is unchanged

def test_findings_comparison_detects_added_removed_and_unchanged() -> None:
    previous = InspectionResult()
    current = InspectionResult()

    previous.add_many(
        [
            _finding("shared", Severity.WARNING),
            _finding("removed", Severity.ERROR),
        ]
    )

    current.add_many(
        [
            _finding("shared", Severity.WARNING),
            _finding("added", Severity.INFO),
        ]
    )

    comparison = InspectionComparison(
        previous=previous,
        current=current,
    )

    assert [f.finding_id for f in comparison.findings.added] == [
        "added"
    ]
    assert [f.finding_id for f in comparison.findings.removed] == [
        "removed"
    ]
    assert [f.finding_id for f in comparison.findings.unchanged] == [
        "shared"
    ]

def test_category_comparison_worsened() -> None:
    comparison = CategoryComparison(
        previous_score=90,
        current_score=70,
        previous_status=HealthStatus.EXCELLENT,
        current_status=HealthStatus.FAIR,
    )

    assert comparison.score_delta == -20
    assert comparison.worsened
    assert not comparison.improved
    assert not comparison.unchanged


def test_category_comparison_unchanged() -> None:
    comparison = CategoryComparison(
        previous_score=90,
        current_score=90,
        previous_status=HealthStatus.EXCELLENT,
        current_status=HealthStatus.EXCELLENT,
    )

    assert comparison.score_delta == 0
    assert comparison.unchanged
    assert not comparison.improved
    assert not comparison.worsened

def test_categories_comparison() -> None:
    previous = InspectionResult()
    current = InspectionResult()

    previous.record_rule(
        category="storage",
        weight=20,
        findings=[
            _finding("storage.error", Severity.ERROR),
        ],
    )

    current.record_rule(
        category="storage",
        weight=10,
        findings=[
            _finding("storage.warning", Severity.WARNING),
        ],
    )

    comparison = InspectionComparison(
        previous=previous,
        current=current,
    )

    storage = comparison.categories["storage"]

    assert storage.previous_score == 86
    assert storage.current_score == 97
    assert storage.score_delta == 11
    assert storage.previous_status is HealthStatus.GOOD
    assert storage.current_status is HealthStatus.EXCELLENT
    assert storage.improved