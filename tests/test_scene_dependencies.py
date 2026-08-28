"""Tests for scene dependency inspection helpers."""

from custom_components.ha_inspector.engine.scene_dependencies import (
    SceneDependency,
    scene_dependency_from_entities,
)


def test_scene_dependency_exposes_referenced_entities() -> None:
    """Scene dependencies expose unique entity IDs in reference order."""
    dependency = scene_dependency_from_entities(
        "scene.evening",
        "Evening",
        [
            "light.living_room",
            "switch.ambient_light",
            "light.living_room",
        ],
    )

    assert isinstance(dependency, SceneDependency)
    assert dependency.scene_entity_id == "scene.evening"
    assert dependency.name == "Evening"
    assert dependency.referenced_entities == (
        "light.living_room",
        "switch.ambient_light",
    )
    assert dependency.referenced_entity_count == 2


def test_scene_dependency_sorts_resolved_entities() -> None:
    """Resolved scene entities have deterministic ordering."""
    dependency = scene_dependency_from_entities(
        "scene.movie",
        "Movie",
        [
            "switch.tv",
            "light.living_room",
            "media_player.television",
        ],
    )

    assert dependency.referenced_entities == (
        "light.living_room",
        "media_player.television",
        "switch.tv",
    )


def test_scene_dependency_supports_no_references() -> None:
    """A scene can expose no resolved entity dependencies."""
    dependency = scene_dependency_from_entities(
        "scene.empty",
        "Empty",
        [],
    )

    assert dependency.references == ()
    assert dependency.referenced_entities == ()
    assert dependency.referenced_entity_count == 0
