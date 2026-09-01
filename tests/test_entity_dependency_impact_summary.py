"""Tests for per-entity dependency impact summaries."""

from custom_components.ha_inspector.engine import (
    entity_dependency_impact_summary as impact_summary,
)
from custom_components.ha_inspector.engine.stale_reference_context import (
    StaleReferenceContext,
)


def test_build_entity_dependency_impact_summary() -> None:
    context = StaleReferenceContext(
        entity_id="sensor.missing",
        active_automation_references=(
            "automation.first",
            "automation.second",
        ),
        disabled_automation_references=("automation.disabled",),
        active_script_references=("script.active",),
        disabled_script_references=(),
        active_scene_references=(),
        disabled_scene_references=("scene.disabled",),
    )

    assert impact_summary.build_entity_dependency_impact_summary(
        context
    ) == impact_summary.EntityDependencyImpactSummary(
        entity_id="sensor.missing",
        reference_count=5,
        active_reference_count=3,
        disabled_reference_count=2,
        automation_reference_count=3,
        script_reference_count=1,
        scene_reference_count=1,
    )


def test_build_entity_dependency_impact_summary_handles_no_references() -> None:
    context = StaleReferenceContext(
        entity_id="sensor.missing",
        active_automation_references=(),
        disabled_automation_references=(),
        active_script_references=(),
        disabled_script_references=(),
        active_scene_references=(),
        disabled_scene_references=(),
    )

    assert impact_summary.build_entity_dependency_impact_summary(
        context
    ) == impact_summary.EntityDependencyImpactSummary(
        entity_id="sensor.missing",
        reference_count=0,
        active_reference_count=0,
        disabled_reference_count=0,
        automation_reference_count=0,
        script_reference_count=0,
        scene_reference_count=0,
    )


def test_build_entity_dependency_impact_summaries_preserves_order() -> None:
    contexts = (
        StaleReferenceContext(
            entity_id="sensor.alpha",
            active_automation_references=("automation.first",),
            disabled_automation_references=(),
            active_script_references=(),
            disabled_script_references=(),
            active_scene_references=(),
            disabled_scene_references=(),
        ),
        StaleReferenceContext(
            entity_id="sensor.beta",
            active_automation_references=(),
            disabled_automation_references=(),
            active_script_references=("script.first",),
            disabled_script_references=(),
            active_scene_references=(),
            disabled_scene_references=(),
        ),
    )

    summaries = impact_summary.build_entity_dependency_impact_summaries(
        contexts
    )

    assert tuple(summary.entity_id for summary in summaries) == (
        "sensor.alpha",
        "sensor.beta",
    )


def test_build_entity_dependency_impact_summaries_handles_empty_input() -> None:
    assert impact_summary.build_entity_dependency_impact_summaries(()) == ()
