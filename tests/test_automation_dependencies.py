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


def test_automation_dependency_ignores_internal_entity_registry_ids() -> None:
    dependency = automation_dependency_from_entities(
        "automation.device_condition",
        "Device condition",
        [
            "57324feedae07b0428d144cd73013d02",
            "binary_sensor.motion",
            "d7aef9f16fa6d992ead4c5d905b34247",
            "e896fe3b3a7d1eb58e306aa01b68fc38",
        ],
    )

    assert dependency.references == (
        EntityReference(
            entity_id="binary_sensor.motion",
            path=(),
        ),
    )
    assert dependency.referenced_entities == (
        "binary_sensor.motion",
    )
    assert dependency.referenced_entity_count == 1
