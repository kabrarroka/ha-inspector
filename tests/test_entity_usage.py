"""Tests for known entity usage inspection helpers."""

from custom_components.ha_inspector.engine.entity_usage import (
    missing_entity_ids,
    referenced_entity_ids,
    unreferenced_entity_ids,
)


def test_referenced_entity_ids_combines_dependency_sources() -> None:
    assert referenced_entity_ids(
        [
            ["sensor.temperature", "light.kitchen"],
            ["light.kitchen", "media_player.tv"],
            ["binary_sensor.motion"],
        ]
    ) == {
        "binary_sensor.motion",
        "light.kitchen",
        "media_player.tv",
        "sensor.temperature",
    }


def test_referenced_entity_ids_handles_empty_dependencies() -> None:
    assert referenced_entity_ids([]) == set()


def test_unreferenced_entity_ids_returns_unknown_usage_candidates() -> None:
    assert unreferenced_entity_ids(
        [
            "sensor.temperature",
            "sensor.humidity",
            "light.kitchen",
        ],
        [
            "sensor.temperature",
            "light.kitchen",
        ],
    ) == ("sensor.humidity",)


def test_unreferenced_entity_ids_excludes_configuration_domains() -> None:
    assert unreferenced_entity_ids(
        [
            "automation.kitchen",
            "script.evening",
            "scene.movie",
            "sensor.temperature",
        ],
        [],
    ) == ("sensor.temperature",)


def test_unreferenced_entity_ids_deduplicates_and_sorts() -> None:
    assert unreferenced_entity_ids(
        [
            "sensor.z",
            "sensor.a",
            "sensor.z",
        ],
        [],
    ) == (
        "sensor.a",
        "sensor.z",
    )


def test_unreferenced_entity_ids_handles_empty_entities() -> None:
    assert unreferenced_entity_ids([], ["sensor.temperature"]) == ()


def test_missing_entity_ids_returns_unknown_references() -> None:
    assert missing_entity_ids(
        [
            "sensor.temperature",
            "light.kitchen",
            "switch.missing",
        ],
        [
            "sensor.temperature",
            "light.kitchen",
        ],
    ) == ("switch.missing",)


def test_missing_entity_ids_deduplicates_and_sorts() -> None:
    assert missing_entity_ids(
        [
            "sensor.z_missing",
            "sensor.a_missing",
            "sensor.z_missing",
        ],
        [],
    ) == (
        "sensor.a_missing",
        "sensor.z_missing",
    )


def test_missing_entity_ids_handles_all_existing() -> None:
    assert missing_entity_ids(
        [
            "sensor.temperature",
            "light.kitchen",
        ],
        [
            "sensor.temperature",
            "light.kitchen",
        ],
    ) == ()


def test_missing_entity_ids_handles_empty_references() -> None:
    assert missing_entity_ids([], ["sensor.temperature"]) == ()
