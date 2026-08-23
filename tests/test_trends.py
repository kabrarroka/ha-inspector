"""Tests for historical trend analysis."""

from custom_components.ha_inspector.engine.trends import (
    ScoreTrend,
    health_score_trend,
)


def test_score_trend_requires_two_samples() -> None:
    assert health_score_trend([]) == ScoreTrend(
        direction="insufficient_data",
        samples=0,
        first_score=None,
        last_score=None,
        delta=None,
    )

    assert health_score_trend([{"score": 90}]) == ScoreTrend(
        direction="insufficient_data",
        samples=1,
        first_score=90,
        last_score=90,
        delta=None,
    )


def test_score_trend_detects_improvement() -> None:
    trend = health_score_trend(
        [
            {"score": 70},
            {"score": 80},
            {"score": 95},
        ]
    )

    assert trend.direction == "improving"
    assert trend.samples == 3
    assert trend.first_score == 70
    assert trend.last_score == 95
    assert trend.delta == 25


def test_score_trend_detects_decline() -> None:
    trend = health_score_trend(
        [
            {"score": 95},
            {"score": 90},
            {"score": 75},
        ]
    )

    assert trend.direction == "declining"
    assert trend.delta == -20


def test_score_trend_detects_stability() -> None:
    trend = health_score_trend(
        [
            {"score": 88},
            {"score": 91},
            {"score": 88},
        ]
    )

    assert trend.direction == "stable"
    assert trend.delta == 0


def test_score_trend_ignores_invalid_scores() -> None:
    trend = health_score_trend(
        [
            {"score": None},
            {"score": "90"},
            {"score": True},
            {},
            {"score": 80},
            {"score": 90},
        ]
    )

    assert trend == ScoreTrend(
        direction="improving",
        samples=2,
        first_score=80,
        last_score=90,
        delta=10,
    )


def test_score_trend_serializes() -> None:
    trend = ScoreTrend(
        direction="improving",
        samples=3,
        first_score=70,
        last_score=90,
        delta=20,
    )

    assert trend.as_dict() == {
        "direction": "improving",
        "samples": 3,
        "first_score": 70,
        "last_score": 90,
        "delta": 20,
    }
