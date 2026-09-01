"""Tests for stale reference investigation context helpers."""

from custom_components.ha_inspector.engine import (
    stale_reference_context as stale_context,
)


def test_build_stale_reference_contexts_groups_reference_status() -> None:
    assert stale_context.build_stale_reference_contexts(
        ["sensor.missing", "switch.missing"],
        [
            (
                "automation.active",
                ["sensor.missing", "light.kitchen"],
                False,
            ),
            (
                "automation.disabled",
                ["sensor.missing", "switch.missing"],
                True,
            ),
        ],
        [
            (
                "script.active",
                ["sensor.missing"],
                False,
            ),
            (
                "script.disabled",
                ["switch.missing"],
                True,
            ),
        ],
        [
            (
                "scene.active",
                ["switch.missing"],
                False,
            )
        ],
    ) == (
        stale_context.StaleReferenceContext(
            entity_id="sensor.missing",
            active_automation_references=("automation.active",),
            disabled_automation_references=("automation.disabled",),
            active_script_references=("script.active",),
            disabled_script_references=(),
            active_scene_references=(),
            disabled_scene_references=(),
        ),
        stale_context.StaleReferenceContext(
            entity_id="switch.missing",
            active_automation_references=(),
            disabled_automation_references=("automation.disabled",),
            active_script_references=(),
            disabled_script_references=("script.disabled",),
            active_scene_references=("scene.active",),
            disabled_scene_references=(),
        ),
    )


def test_build_stale_reference_contexts_deduplicates_and_sorts() -> None:
    contexts = stale_context.build_stale_reference_contexts(
        ["sensor.missing", "sensor.missing"],
        [
            (
                "automation.z_rule",
                ["sensor.missing", "sensor.missing"],
                False,
            ),
            (
                "automation.a_rule",
                ["sensor.missing"],
                False,
            ),
            (
                "automation.z_rule",
                ["sensor.missing"],
                False,
            ),
        ],
        [],
        [],
    )

    assert contexts == (
        stale_context.StaleReferenceContext(
            entity_id="sensor.missing",
            active_automation_references=(
                "automation.a_rule",
                "automation.z_rule",
            ),
            disabled_automation_references=(),
            active_script_references=(),
            disabled_script_references=(),
            active_scene_references=(),
            disabled_scene_references=(),
        ),
    )


def test_build_stale_reference_contexts_keeps_missing_entities_without_sources(
) -> None:
    assert stale_context.build_stale_reference_contexts(
        ["sensor.missing"],
        [],
        [],
        [],
    ) == (
        stale_context.StaleReferenceContext(
            entity_id="sensor.missing",
            active_automation_references=(),
            disabled_automation_references=(),
            active_script_references=(),
            disabled_script_references=(),
            active_scene_references=(),
            disabled_scene_references=(),
        ),
    )


def test_build_stale_reference_contexts_handles_empty_input() -> None:
    assert stale_context.build_stale_reference_contexts(
        [],
        [],
        [],
        [],
    ) == ()


def test_stale_reference_context_handles_one_shot_entity_iterables() -> None:
    contexts = stale_context.build_stale_reference_contexts(
        ("sensor.alpha", "sensor.beta"),
        (
            (
                "automation.shared",
                iter(("sensor.beta", "sensor.alpha")),
                False,
            ),
        ),
        (),
        (),
    )

    assert contexts == (
        stale_context.StaleReferenceContext(
            entity_id="sensor.alpha",
            active_automation_references=("automation.shared",),
            disabled_automation_references=(),
            active_script_references=(),
            disabled_script_references=(),
            active_scene_references=(),
            disabled_scene_references=(),
        ),
        stale_context.StaleReferenceContext(
            entity_id="sensor.beta",
            active_automation_references=("automation.shared",),
            disabled_automation_references=(),
            active_script_references=(),
            disabled_script_references=(),
            active_scene_references=(),
            disabled_scene_references=(),
        ),
    )
