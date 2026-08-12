"""Tests for the HA Inspector health score helpers."""

from custom_components.ha_inspector.engine.score import (
    HealthStatus,
    ScoreCalculator,
    ScoringEntry,
    category_score,
    score_from_penalties,
    status_for_score,
)
from custom_components.ha_inspector.engine.severity import Severity


def test_score_from_empty_penalties_is_perfect() -> None:
    """An inspection without penalties has a perfect score."""
    assert score_from_penalties({}) == 100


def test_score_never_drops_below_zero() -> None:
    """The overall score must never become negative."""
    assert score_from_penalties({"system": 150.0}) == 0


def test_category_score_never_drops_below_zero() -> None:
    """A category score must never become negative."""
    assert category_score(125.0) == 0


def test_health_status_boundaries() -> None:
    """Scores map to the expected qualitative statuses."""
    assert status_for_score(100) is HealthStatus.EXCELLENT
    assert status_for_score(90) is HealthStatus.EXCELLENT
    assert status_for_score(89) is HealthStatus.GOOD
    assert status_for_score(75) is HealthStatus.GOOD
    assert status_for_score(74) is HealthStatus.FAIR
    assert status_for_score(50) is HealthStatus.FAIR
    assert status_for_score(49) is HealthStatus.POOR
    assert status_for_score(25) is HealthStatus.POOR
    assert status_for_score(24) is HealthStatus.CRITICAL
    assert status_for_score(0) is HealthStatus.CRITICAL

def test_score_calculator_from_scoring_entries() -> None:
    """Health score can be calculated from scoring entries."""
    entries = [
        ScoringEntry(
            category="recorder",
            weight=10,
            severity=Severity.WARNING,
        )
    ]

    health = ScoreCalculator.calculate_entries(entries)

    assert health.score == 97
    assert health.max_score == 100
    assert health.penalty == 3.0
    assert health.status is HealthStatus.EXCELLENT