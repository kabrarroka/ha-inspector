"""Tests for automation dependency inspection."""

from custom_components.ha_inspector.engine.automation_dependencies import (
    automation_dependency_from_entities,
)
from custom_components.ha_inspector.engine.entity_references import EntityReference


def test_automation_dependency_from_resolved_entities() -> None:
    dependency = automation_dependency_from_entities(
        "automation.kitchen",
        "Kitchen",
        [
            "light.kitchen",
            "binary_sensor.motion",
            "light.kitchen",
        ],
    )

    assert dependency.automation_entity_id == "automation.kitchen"
    assert dependency.name == "Kitchen"
    assert dependency.references == (
        EntityReference(
            entity_id="binary_sensor.motion",
            path=(),
        ),
        EntityReference(
            entity_id="light.kitchen",
            path=(),
        ),
    )
    assert dependency.referenced_entities == (
        "binary_sensor.motion",
        "light.kitchen",
    )
    assert dependency.referenced_entity_count == 2


def test_automation_dependency_from_resolved_entities_empty() -> None:
    dependency = automation_dependency_from_entities(
        "automation.empty",
        "Empty",
        [],
    )

    assert dependency.references == ()
    assert dependency.referenced_entities == ()
    assert dependency.referenced_entity_count == 0
