"""Tests for entity reference discovery."""

from custom_components.ha_inspector.engine.entity_references import (
    EntityReference,
    discover_entity_references,
)


def test_discover_entity_references_from_string() -> None:
    assert discover_entity_references("sensor.temperature") == [
        EntityReference(
            entity_id="sensor.temperature",
            path=(),
        )
    ]


def test_discover_entity_references_from_nested_configuration() -> None:
    config = {
        "trigger": {
            "entity_id": "binary_sensor.motion",
        },
        "actions": [
            {
                "target": {
                    "entity_id": [
                        "light.kitchen",
                        "light.hall",
                    ]
                }
            }
        ],
    }

    assert discover_entity_references(config) == [
        EntityReference(
            entity_id="binary_sensor.motion",
            path=("trigger", "entity_id"),
        ),
        EntityReference(
            entity_id="light.kitchen",
            path=("actions", 0, "target", "entity_id", 0),
        ),
        EntityReference(
            entity_id="light.hall",
            path=("actions", 0, "target", "entity_id", 1),
        ),
    ]


def test_discover_entity_references_from_embedded_text() -> None:
    value = "Compare sensor.indoor_temperature with sensor.outdoor_temperature."

    assert discover_entity_references(value) == [
        EntityReference(
            entity_id="sensor.indoor_temperature",
            path=(),
        ),
        EntityReference(
            entity_id="sensor.outdoor_temperature",
            path=(),
        ),
    ]


def test_discover_entity_references_deduplicates_same_path() -> None:
    value = "sensor.temperature sensor.temperature"

    assert discover_entity_references(value) == [
        EntityReference(
            entity_id="sensor.temperature",
            path=(),
        )
    ]


def test_discover_entity_references_keeps_same_entity_at_different_paths() -> None:
    config = {
        "first": "sensor.temperature",
        "second": "sensor.temperature",
    }

    assert discover_entity_references(config) == [
        EntityReference(
            entity_id="sensor.temperature",
            path=("first",),
        ),
        EntityReference(
            entity_id="sensor.temperature",
            path=("second",),
        ),
    ]


def test_discover_entity_references_ignores_non_entity_values() -> None:
    config = {
        "enabled": True,
        "count": 3,
        "missing": None,
        "values": ["plain text", 4.2],
    }

    assert discover_entity_references(config) == []


def test_discover_entity_references_rejects_invalid_candidate_shapes() -> None:
    value = [
        "Sensor.Temperature",
        "sensor",
        "sensor.",
        ".temperature",
        "sensor.temperature-extra",
    ]

    assert discover_entity_references(value) == []
