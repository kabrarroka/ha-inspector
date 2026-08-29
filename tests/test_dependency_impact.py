"""Tests for dependency impact scoring and prioritization."""

from custom_components.ha_inspector.engine.dependency_impact import (
    dependency_impact_score,
    dependency_priority,
)


def test_dependency_impact_score_for_unknown_dependency() -> None:
    assert (
        dependency_impact_score(
            state="unknown",
            reference_count=1,
        )
        == 15
    )
    assert (
        dependency_impact_score(
            state="unknown",
            reference_count=3,
        )
        == 25
    )


def test_dependency_impact_score_for_unavailable_dependency() -> None:
    assert (
        dependency_impact_score(
            state="unavailable",
            reference_count=1,
        )
        == 25
    )
    assert (
        dependency_impact_score(
            state="unavailable",
            reference_count=3,
        )
        == 35
    )


def test_dependency_impact_score_caps_reference_count() -> None:
    assert (
        dependency_impact_score(
            state="unavailable",
            reference_count=10,
        )
        == 70
    )
    assert (
        dependency_impact_score(
            state="unavailable",
            reference_count=100,
        )
        == 70
    )


def test_dependency_impact_score_normalizes_negative_reference_count() -> None:
    assert (
        dependency_impact_score(
            state="unknown",
            reference_count=-1,
        )
        == 10
    )


def test_dependency_priority() -> None:
    assert dependency_priority(0) == "low"
    assert dependency_priority(19) == "low"
    assert dependency_priority(20) == "medium"
    assert dependency_priority(34) == "medium"
    assert dependency_priority(35) == "high"
    assert dependency_priority(49) == "high"
    assert dependency_priority(50) == "critical"


def test_dependency_impact_score_for_unrecognized_state() -> None:
    assert (
        dependency_impact_score(
            state="on",
            reference_count=5,
        )
        == 0
    )
