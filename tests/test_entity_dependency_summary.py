"""Tests for entity dependency summary helpers."""

from custom_components.ha_inspector.engine.entity_dependency_summary import (
    EntityDependencySummary,
    build_entity_dependency_summaries,
)


def test_build_entity_dependency_summaries_combines_sources() -> None:
    assert build_entity_dependency_summaries(
        [
            (
                "automation.kitchen",
                [
                    "light.kitchen",
                    "sensor.temperature",
                ],
            )
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
        EntityDependencySummary(
            entity_id="light.kitchen",
            reference_count=3,
            automation_references=("automation.kitchen",),
            script_references=("script.evening",),
            scene_references=("scene.movie",),
        ),
        EntityDependencySummary(
            entity_id="sensor.temperature",
            reference_count=1,
            automation_references=("automation.kitchen",),
            script_references=(),
            scene_references=(),
        ),
        EntityDependencySummary(
            entity_id="switch.fan",
            reference_count=1,
            automation_references=(),
            script_references=("script.evening",),
            scene_references=(),
        ),
    )


def test_build_entity_dependency_summaries_deduplicates_source_references() -> None:
    assert build_entity_dependency_summaries(
        [
            (
                "automation.kitchen",
                [
                    "light.kitchen",
                    "light.kitchen",
                ],
            ),
            (
                "automation.kitchen",
                [
                    "light.kitchen",
                ],
            ),
        ],
        [],
        [],
    ) == (
        EntityDependencySummary(
            entity_id="light.kitchen",
            reference_count=1,
            automation_references=("automation.kitchen",),
            script_references=(),
            scene_references=(),
        ),
    )


def test_build_entity_dependency_summaries_sorts_sources() -> None:
    summaries = build_entity_dependency_summaries(
        [
            ("automation.z_last", ["sensor.temperature"]),
            ("automation.a_first", ["sensor.temperature"]),
        ],
        [
            ("script.z_last", ["sensor.temperature"]),
            ("script.a_first", ["sensor.temperature"]),
        ],
        [
            ("scene.z_last", ["sensor.temperature"]),
            ("scene.a_first", ["sensor.temperature"]),
        ],
    )

    assert summaries[0].automation_references == (
        "automation.a_first",
        "automation.z_last",
    )
    assert summaries[0].script_references == (
        "script.a_first",
        "script.z_last",
    )
    assert summaries[0].scene_references == (
        "scene.a_first",
        "scene.z_last",
    )
    assert summaries[0].reference_count == 6


def test_build_entity_dependency_summaries_sorts_entities() -> None:
    summaries = build_entity_dependency_summaries(
        [
            (
                "automation.example",
                [
                    "sensor.z_last",
                    "sensor.a_first",
                ],
            )
        ],
        [],
        [],
    )

    assert tuple(summary.entity_id for summary in summaries) == (
        "sensor.a_first",
        "sensor.z_last",
    )


def test_build_entity_dependency_summaries_handles_empty_input() -> None:
    assert build_entity_dependency_summaries([], [], []) == ()
