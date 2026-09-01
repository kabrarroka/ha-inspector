"""Tests for configuration dependency summary helpers."""

from custom_components.ha_inspector.engine.configuration_dependency_summary import (
    ConfigurationDependencySummary,
    build_configuration_dependency_summaries,
)


def test_build_configuration_dependency_summaries_groups_by_type() -> None:
    assert build_configuration_dependency_summaries(
        [
            (
                "automation.kitchen",
                [
                    "light.kitchen",
                    "sensor.temperature",
                ],
            ),
            (
                "automation.evening",
                [
                    "light.kitchen",
                    "switch.fan",
                ],
            ),
        ],
        [
            (
                "script.evening",
                [
                    "light.kitchen",
                    "switch.fan",
                ],
            )
        ],
        [
            (
                "scene.movie",
                [
                    "light.kitchen",
                ],
            )
        ],
    ) == (
        ConfigurationDependencySummary(
            configuration_type="automation",
            configuration_count=2,
            referenced_entity_count=3,
            reference_count=4,
        ),
        ConfigurationDependencySummary(
            configuration_type="script",
            configuration_count=1,
            referenced_entity_count=2,
            reference_count=2,
        ),
        ConfigurationDependencySummary(
            configuration_type="scene",
            configuration_count=1,
            referenced_entity_count=1,
            reference_count=1,
        ),
    )


def test_build_configuration_dependency_summaries_deduplicates_references() -> None:
    assert build_configuration_dependency_summaries(
        [
            (
                "automation.kitchen",
                [
                    "light.kitchen",
                    "light.kitchen",
                ],
            )
        ],
        [],
        [],
    ) == (
        ConfigurationDependencySummary(
            configuration_type="automation",
            configuration_count=1,
            referenced_entity_count=1,
            reference_count=1,
        ),
        ConfigurationDependencySummary(
            configuration_type="script",
            configuration_count=0,
            referenced_entity_count=0,
            reference_count=0,
        ),
        ConfigurationDependencySummary(
            configuration_type="scene",
            configuration_count=0,
            referenced_entity_count=0,
            reference_count=0,
        ),
    )


def test_build_configuration_dependency_summaries_handles_empty_input() -> None:
    assert build_configuration_dependency_summaries([], [], []) == (
        ConfigurationDependencySummary(
            configuration_type="automation",
            configuration_count=0,
            referenced_entity_count=0,
            reference_count=0,
        ),
        ConfigurationDependencySummary(
            configuration_type="script",
            configuration_count=0,
            referenced_entity_count=0,
            reference_count=0,
        ),
        ConfigurationDependencySummary(
            configuration_type="scene",
            configuration_count=0,
            referenced_entity_count=0,
            reference_count=0,
        ),
    )
