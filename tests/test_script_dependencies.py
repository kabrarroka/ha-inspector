"""Tests for script dependency inspection."""

from custom_components.ha_inspector.engine.entity_references import EntityReference
from custom_components.ha_inspector.engine.script_dependencies import (
    script_dependency_from_entities,
)


def test_script_dependency_from_resolved_entities() -> None:
    dependency = script_dependency_from_entities(
        "script.evening",
        "Evening",
        [
            "light.living_room",
            "media_player.tv",
            "light.living_room",
        ],
    )

    assert dependency.script_entity_id == "script.evening"
    assert dependency.name == "Evening"
    assert dependency.references == (
        EntityReference(
            entity_id="light.living_room",
            path=(),
        ),
        EntityReference(
            entity_id="media_player.tv",
            path=(),
        ),
    )
    assert dependency.referenced_entities == (
        "light.living_room",
        "media_player.tv",
    )
    assert dependency.referenced_entity_count == 2


def test_script_dependency_from_resolved_entities_empty() -> None:
    dependency = script_dependency_from_entities(
        "script.empty",
        "Empty",
        [],
    )

    assert dependency.references == ()
    assert dependency.referenced_entities == ()
    assert dependency.referenced_entity_count == 0


def test_script_dependency_ignores_internal_entity_registry_ids() -> None:
    dependency = script_dependency_from_entities(
        "script.device_action",
        "Device action",
        [
            "57324feedae07b0428d144cd73013d02",
            "light.kitchen",
        ],
    )

    assert dependency.references == (
        EntityReference(
            entity_id="light.kitchen",
            path=(),
        ),
    )
    assert dependency.referenced_entities == (
        "light.kitchen",
    )
    assert dependency.referenced_entity_count == 1
