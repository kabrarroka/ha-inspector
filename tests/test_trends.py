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


def test_domain_health_trends_detect_per_domain_changes() -> None:
    from custom_components.ha_inspector.engine.trends import (
        domain_health_trends,
    )

    trends = domain_health_trends(
        [
            {
                "domain_health": {
                    "storage": {
                        "health": {
                            "score": 70,
                        }
                    },
                    "system": {
                        "health": {
                            "score": 95,
                        }
                    },
                }
            },
            {
                "domain_health": {
                    "storage": {
                        "health": {
                            "score": 90,
                        }
                    },
                    "system": {
                        "health": {
                            "score": 80,
                        }
                    },
                }
            },
        ]
    )

    assert trends["storage"].trend.direction == "improving"
    assert trends["storage"].trend.delta == 20

    assert trends["system"].trend.direction == "declining"
    assert trends["system"].trend.delta == -15


def test_domain_health_trends_report_insufficient_data() -> None:
    from custom_components.ha_inspector.engine.trends import (
        domain_health_trends,
    )

    trends = domain_health_trends(
        [
            {
                "domain_health": {
                    "entities": {
                        "health": {
                            "score": 88,
                        }
                    },
                    "integrations": {
                        "health": None,
                    },
                }
            }
        ]
    )

    assert trends["entities"].trend.direction == "insufficient_data"
    assert trends["entities"].trend.samples == 1
    assert trends["entities"].trend.first_score == 88

    assert trends["integrations"].trend.direction == "insufficient_data"
    assert trends["integrations"].trend.samples == 0


def test_domain_health_trends_ignore_invalid_data() -> None:
    from custom_components.ha_inspector.engine.trends import (
        domain_health_trends,
    )

    trends = domain_health_trends(
        [
            {
                "domain_health": "invalid",
            },
            {
                "domain_health": {
                    123: {
                        "health": {
                            "score": 90,
                        }
                    },
                    "system": "invalid",
                    "storage": {
                        "health": {
                            "score": True,
                        }
                    },
                    "entities": {
                        "health": {
                            "score": "90",
                        }
                    },
                }
            },
        ]
    )

    assert set(trends) == {
        "entities",
        "storage",
    }

    assert "system" not in trends

    assert all(
        trend.trend.direction == "insufficient_data"
        for trend in trends.values()
    )


def test_domain_health_trends_are_sorted() -> None:
    from custom_components.ha_inspector.engine.trends import (
        domain_health_trends,
    )

    trends = domain_health_trends(
        [
            {
                "domain_health": {
                    "system": {
                        "health": {
                            "score": 90,
                        }
                    },
                    "entities": {
                        "health": {
                            "score": 80,
                        }
                    },
                }
            }
        ]
    )

    assert list(trends) == [
        "entities",
        "system",
    ]


def test_domain_trend_serializes() -> None:
    from custom_components.ha_inspector.engine.trends import (
        DomainTrend,
    )

    trend = DomainTrend(
        domain="system",
        trend=ScoreTrend(
            direction="improving",
            samples=3,
            first_score=70,
            last_score=90,
            delta=20,
        ),
    )

    assert trend.as_dict() == {
        "domain": "system",
        "direction": "improving",
        "samples": 3,
        "first_score": 70,
        "last_score": 90,
        "delta": 20,
    }


def test_latest_health_change_detects_recovery() -> None:
    from custom_components.ha_inspector.engine.trends import (
        latest_health_change,
    )

    change = latest_health_change(
        [
            {"score": 70},
            {"score": 75},
            {"score": 90},
        ]
    )

    assert change.kind == "recovery"
    assert change.previous_score == 75
    assert change.current_score == 90
    assert change.delta == 15


def test_latest_health_change_detects_regression() -> None:
    from custom_components.ha_inspector.engine.trends import (
        latest_health_change,
    )

    change = latest_health_change(
        [
            {"score": 95},
            {"score": 90},
            {"score": 72},
        ]
    )

    assert change.kind == "regression"
    assert change.previous_score == 90
    assert change.current_score == 72
    assert change.delta == -18


def test_latest_health_change_detects_stable() -> None:
    from custom_components.ha_inspector.engine.trends import (
        latest_health_change,
    )

    change = latest_health_change(
        [
            {"score": 88},
            {"score": 88},
        ]
    )

    assert change.kind == "stable"
    assert change.delta == 0


def test_latest_health_change_requires_two_valid_scores() -> None:
    from custom_components.ha_inspector.engine.trends import (
        latest_health_change,
    )

    empty = latest_health_change([])
    assert empty.kind == "insufficient_data"
    assert empty.previous_score is None
    assert empty.current_score is None
    assert empty.delta is None

    single = latest_health_change(
        [
            {"score": None},
            {"score": True},
            {"score": 90},
        ]
    )
    assert single.kind == "insufficient_data"
    assert single.previous_score is None
    assert single.current_score == 90
    assert single.delta is None


def test_health_change_serializes() -> None:
    from custom_components.ha_inspector.engine.trends import HealthChange

    change = HealthChange(
        kind="regression",
        previous_score=90,
        current_score=80,
        delta=-10,
    )

    assert change.as_dict() == {
        "kind": "regression",
        "previous_score": 90,
        "current_score": 80,
        "delta": -10,
    }
