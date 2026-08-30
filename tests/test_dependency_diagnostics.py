"""Tests for compact dependency diagnostics."""

from custom_components.ha_inspector.engine.dependency_diagnostics import (
    dependency_diagnostics,
)
from custom_components.ha_inspector.engine.entities_state import (
    DependencyHealthSummary,
    EntitiesState,
)


def _dependency(
    entity_id: str,
    *,
    state: str,
    impact_score: int,
    priority: str,
) -> DependencyHealthSummary:
    return DependencyHealthSummary(
        entity_id=entity_id,
        name=entity_id,
        domain=entity_id.split(".", maxsplit=1)[0],
        state=state,
        impact_score=impact_score,
        priority=priority,
    )


def test_dependency_diagnostics_for_empty_state() -> None:
    """Empty entity state exposes zeroed dependency diagnostics."""
    assert dependency_diagnostics(EntitiesState()) == {
        "affected_entities": 0,
        "unavailable": 0,
        "unknown": 0,
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "max_impact_score": 0,
    }


def test_dependency_diagnostics_aggregates_problematic_dependencies() -> None:
    """Dependency diagnostics aggregate states, priorities and impact."""
    entities = EntitiesState(
        unavailable_dependency_count=2,
        unavailable_dependencies=[
            _dependency(
                "sensor.temperature",
                state="unavailable",
                impact_score=55,
                priority="critical",
            ),
            _dependency(
                "light.kitchen",
                state="unavailable",
                impact_score=40,
                priority="high",
            ),
        ],
        unknown_dependency_count=2,
        unknown_dependencies=[
            _dependency(
                "sensor.humidity",
                state="unknown",
                impact_score=30,
                priority="medium",
            ),
            _dependency(
                "binary_sensor.motion",
                state="unknown",
                impact_score=15,
                priority="low",
            ),
        ],
    )

    assert dependency_diagnostics(entities) == {
        "affected_entities": 4,
        "unavailable": 2,
        "unknown": 2,
        "critical": 1,
        "high": 1,
        "medium": 1,
        "low": 1,
        "max_impact_score": 55,
    }


def test_dependency_diagnostics_ignores_unknown_priority() -> None:
    """Unexpected priority labels do not corrupt known priority counts."""
    entities = EntitiesState(
        unavailable_dependencies=[
            _dependency(
                "sensor.temperature",
                state="unavailable",
                impact_score=25,
                priority="unexpected",
            ),
        ],
    )

    assert dependency_diagnostics(entities) == {
        "affected_entities": 1,
        "unavailable": 1,
        "unknown": 0,
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "max_impact_score": 25,
    }
