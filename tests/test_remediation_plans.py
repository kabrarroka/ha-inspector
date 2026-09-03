"""Tests for per-entity dependency remediation plans."""

from custom_components.ha_inspector.engine import remediation_plans
from custom_components.ha_inspector.engine.stale_reference_context import (
    StaleReferenceContext,
)


def test_build_remediation_plan_for_active_references() -> None:
    context = StaleReferenceContext(
        entity_id="sensor.missing",
        active_automation_references=("automation.active",),
        disabled_automation_references=(),
        active_script_references=("script.active",),
        disabled_script_references=(),
        active_scene_references=(),
        disabled_scene_references=("scene.disabled",),
    )

    assert remediation_plans.build_remediation_plan(
        context
    ) == remediation_plans.RemediationPlan(
        entity_id="sensor.missing",
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=3,
        active_reference_count=2,
        disabled_reference_count=1,
        steps=(
            remediation_plans.RemediationStep(
                configuration_type="automation",
                configuration_id="automation.active",
                status="active",
                action="review_entity_reference",
            ),
            remediation_plans.RemediationStep(
                configuration_type="script",
                configuration_id="script.active",
                status="active",
                action="review_entity_reference",
            ),
            remediation_plans.RemediationStep(
                configuration_type="scene",
                configuration_id="scene.disabled",
                status="disabled",
                action="review_entity_reference",
            ),
        ),
    )


def test_build_remediation_plan_for_disabled_only_references() -> None:
    context = StaleReferenceContext(
        entity_id="sensor.missing",
        active_automation_references=(),
        disabled_automation_references=("automation.disabled",),
        active_script_references=(),
        disabled_script_references=("script.disabled",),
        active_scene_references=(),
        disabled_scene_references=("scene.disabled",),
    )

    assert remediation_plans.build_remediation_plan(
        context
    ) == remediation_plans.RemediationPlan(
        entity_id="sensor.missing",
        action="remove_disabled_references",
        safety="likely_safe",
        reason="Entity is referenced only by disabled configuration",
        reference_count=3,
        active_reference_count=0,
        disabled_reference_count=3,
        steps=(
            remediation_plans.RemediationStep(
                configuration_type="automation",
                configuration_id="automation.disabled",
                status="disabled",
                action="remove_entity_reference",
            ),
            remediation_plans.RemediationStep(
                configuration_type="script",
                configuration_id="script.disabled",
                status="disabled",
                action="remove_entity_reference",
            ),
            remediation_plans.RemediationStep(
                configuration_type="scene",
                configuration_id="scene.disabled",
                status="disabled",
                action="remove_entity_reference",
            ),
        ),
    )


def test_build_remediation_plan_without_references_returns_none() -> None:
    context = StaleReferenceContext(
        entity_id="sensor.unreferenced",
        active_automation_references=(),
        disabled_automation_references=(),
        active_script_references=(),
        disabled_script_references=(),
        active_scene_references=(),
        disabled_scene_references=(),
    )

    assert remediation_plans.build_remediation_plan(context) is None


def test_remediation_steps_have_stable_type_and_status_order() -> None:
    context = StaleReferenceContext(
        entity_id="sensor.missing",
        active_automation_references=(
            "automation.second",
            "automation.first",
        ),
        disabled_automation_references=("automation.disabled",),
        active_script_references=("script.active",),
        disabled_script_references=("script.disabled",),
        active_scene_references=("scene.active",),
        disabled_scene_references=("scene.disabled",),
    )

    plan = remediation_plans.build_remediation_plan(context)

    assert plan is not None
    assert tuple(
        (
            step.configuration_type,
            step.configuration_id,
            step.status,
        )
        for step in plan.steps
    ) == (
        ("automation", "automation.second", "active"),
        ("automation", "automation.first", "active"),
        ("automation", "automation.disabled", "disabled"),
        ("script", "script.active", "active"),
        ("script", "script.disabled", "disabled"),
        ("scene", "scene.active", "active"),
        ("scene", "scene.disabled", "disabled"),
    )


def test_build_remediation_plans_skips_contexts_without_references() -> None:
    contexts = (
        StaleReferenceContext(
            entity_id="sensor.active",
            active_automation_references=("automation.active",),
            disabled_automation_references=(),
            active_script_references=(),
            disabled_script_references=(),
            active_scene_references=(),
            disabled_scene_references=(),
        ),
        StaleReferenceContext(
            entity_id="sensor.unreferenced",
            active_automation_references=(),
            disabled_automation_references=(),
            active_script_references=(),
            disabled_script_references=(),
            active_scene_references=(),
            disabled_scene_references=(),
        ),
        StaleReferenceContext(
            entity_id="sensor.disabled",
            active_automation_references=(),
            disabled_automation_references=(),
            active_script_references=(),
            disabled_script_references=("script.disabled",),
            active_scene_references=(),
            disabled_scene_references=(),
        ),
    )

    plans = remediation_plans.build_remediation_plans(contexts)

    assert tuple(plan.entity_id for plan in plans) == (
        "sensor.active",
        "sensor.disabled",
    )
    assert plans[0].action == "review_active_references"
    assert plans[1].action == "remove_disabled_references"
