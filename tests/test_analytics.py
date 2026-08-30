"""Tests for inspection analytics."""

from __future__ import annotations

from custom_components.ha_inspector.engine.analytics import InspectionAnalytics
from custom_components.ha_inspector.engine.result import InspectionResult
from custom_components.ha_inspector.engine.score import HealthStatus, ScoringEntry
from custom_components.ha_inspector.engine.severity import Severity


def test_analytics_empty_result() -> None:
    result = InspectionResult()
    analytics = InspectionAnalytics(result)

    assert analytics.score == 100
    assert analytics.health_status is HealthStatus.EXCELLENT
    assert analytics.health.as_dict() == {
        "score": 100,
        "max_score": 100,
        "status": "excellent",
        "penalty": 0,
    }
    assert analytics.categories == {}
    assert analytics.health_summary == {
        "excellent": 0,
        "good": 0,
        "fair": 0,
        "poor": 0,
        "critical": 0,
    }


def test_analytics_calculates_global_health() -> None:
    result = InspectionResult(
        scoring_entries=[
            ScoringEntry(
                category="system",
                weight=20,
                severity=Severity.WARNING,
            ),
            ScoringEntry(
                category="storage",
                weight=30,
                severity=Severity.ERROR,
            ),
        ]
    )

    analytics = InspectionAnalytics(result)

    assert analytics.health.penalty == 27.0
    assert analytics.score == 73
    assert analytics.health_status is HealthStatus.FAIR


def test_analytics_groups_categories() -> None:
    result = InspectionResult(
        category_checks={
            "storage": 2,
            "system": 3,
        },
        category_findings={
            "storage": 1,
            "system": 2,
        },
        scoring_entries=[
            ScoringEntry(
                category="system",
                weight=20,
                severity=Severity.WARNING,
            ),
            ScoringEntry(
                category="system",
                weight=10,
                severity=Severity.ERROR,
            ),
            ScoringEntry(
                category="storage",
                weight=25,
                severity=Severity.CRITICAL,
            ),
        ],
    )

    categories = InspectionAnalytics(result).categories

    assert list(categories) == ["storage", "system"]

    assert categories["storage"] == {
        "health": {
            "score": 75,
            "max_score": 100,
            "status": "good",
            "penalty": 25.0,
        },
        "checks": 2,
        "findings": 1,
    }

    assert categories["system"] == {
        "health": {
            "score": 87,
            "max_score": 100,
            "status": "good",
            "penalty": 13.0,
        },
        "checks": 3,
        "findings": 2,
    }


def test_analytics_health_summary_counts_categories() -> None:
    result = InspectionResult(
        category_checks={
            "critical": 1,
            "excellent": 1,
            "fair": 1,
            "good": 1,
            "poor": 1,
        },
        scoring_entries=[
            ScoringEntry(
                category="excellent",
                weight=10,
                severity=Severity.WARNING,
            ),
            ScoringEntry(
                category="good",
                weight=25,
                severity=Severity.CRITICAL,
            ),
            ScoringEntry(
                category="fair",
                weight=50,
                severity=Severity.CRITICAL,
            ),
            ScoringEntry(
                category="poor",
                weight=75,
                severity=Severity.CRITICAL,
            ),
            ScoringEntry(
                category="critical",
                weight=100,
                severity=Severity.CRITICAL,
            ),
        ],
    )

    assert InspectionAnalytics(result).health_summary == {
        "excellent": 1,
        "good": 1,
        "fair": 1,
        "poor": 1,
        "critical": 1,
    }

def test_domain_health_exposes_primary_domains() -> None:
    """Primary user-facing health domains are always exposed."""
    result = InspectionResult(
        category_checks={
            "storage": 2,
            "system": 1,
        },
        category_findings={
            "storage": 1,
            "system": 0,
        },
        scoring_entries=[
            ScoringEntry(
                category="storage",
                weight=20,
                severity=Severity.WARNING,
            ),
        ],
    )

    domain_health = InspectionAnalytics(result).domain_health

    assert list(domain_health) == [
        "storage",
        "system",
        "integrations",
        "entities",
    ]

    assert domain_health["storage"] == {
        "domain": "storage",
        "status": "checked",
        "health": {
            "score": 94,
            "max_score": 100,
            "status": "excellent",
            "penalty": 6.0,
        },
        "checks": 2,
        "findings": 1,
    }

    assert domain_health["system"] == {
        "domain": "system",
        "status": "checked",
        "health": {
            "score": 100,
            "max_score": 100,
            "status": "excellent",
            "penalty": 0,
        },
        "checks": 1,
        "findings": 0,
    }


def test_domain_health_marks_unchecked_domains() -> None:
    """Domains not inspected are distinct from healthy domains."""
    result = InspectionResult()

    domain_health = InspectionAnalytics(result).domain_health

    for domain in (
        "storage",
        "system",
        "integrations",
        "entities",
    ):
        expected = {
            "domain": domain,
            "status": "not_checked",
            "health": None,
            "checks": 0,
            "findings": 0,
        }

        if domain == "entities":
            expected["dependencies"] = result.dependency_diagnostics

        assert domain_health[domain] == expected


def test_domain_health_ignores_non_primary_categories() -> None:
    """Non-primary categories do not appear in domain summaries."""
    result = InspectionResult(
        category_checks={
            "recorder": 1,
            "database": 1,
        },
    )

    domain_health = InspectionAnalytics(result).domain_health

    assert "recorder" not in domain_health
    assert "database" not in domain_health



def test_domain_health_exposes_entity_dependency_diagnostics() -> None:
    """Entity domain health exposes dependency diagnostics."""
    result = InspectionResult(
        dependency_diagnostics={
            "affected_entities": 3,
            "unavailable": 2,
            "unknown": 1,
            "critical": 1,
            "high": 1,
            "medium": 1,
            "low": 0,
            "max_impact_score": 55,
        }
    )

    dependencies = InspectionAnalytics(result).domain_health[
        "entities"
    ]["dependencies"]

    assert dependencies == {
        "affected_entities": 3,
        "unavailable": 2,
        "unknown": 1,
        "critical": 1,
        "high": 1,
        "medium": 1,
        "low": 0,
        "max_impact_score": 55,
    }
