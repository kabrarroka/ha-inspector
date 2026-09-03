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



def test_group_remediation_actions_by_affected_configuration() -> None:
    plans = (
        remediation_plans.RemediationPlan(
            entity_id="sensor.temperature_missing",
            action="review_active_references",
            safety="review_required",
            reason="Entity is referenced by active configuration",
            reference_count=2,
            active_reference_count=2,
            disabled_reference_count=0,
            steps=(
                remediation_plans.RemediationStep(
                    configuration_type="automation",
                    configuration_id="automation.kitchen",
                    status="active",
                    action="review_entity_reference",
                ),
                remediation_plans.RemediationStep(
                    configuration_type="script",
                    configuration_id="script.evening",
                    status="active",
                    action="review_entity_reference",
                ),
            ),
        ),
        remediation_plans.RemediationPlan(
            entity_id="switch.fan_missing",
            action="review_active_references",
            safety="review_required",
            reason="Entity is referenced by active configuration",
            reference_count=1,
            active_reference_count=1,
            disabled_reference_count=0,
            steps=(
                remediation_plans.RemediationStep(
                    configuration_type="automation",
                    configuration_id="automation.kitchen",
                    status="active",
                    action="review_entity_reference",
                ),
            ),
        ),
    )

    assert remediation_plans.group_remediation_actions(
        plans
    ) == (
        remediation_plans.ConfigurationRemediationActions(
            configuration_type="automation",
            configuration_id="automation.kitchen",
            status="active",
            actions=(
                remediation_plans.ConfigurationRemediationAction(
                    entity_id="sensor.temperature_missing",
                    action="review_entity_reference",
                ),
                remediation_plans.ConfigurationRemediationAction(
                    entity_id="switch.fan_missing",
                    action="review_entity_reference",
                ),
            ),
        ),
        remediation_plans.ConfigurationRemediationActions(
            configuration_type="script",
            configuration_id="script.evening",
            status="active",
            actions=(
                remediation_plans.ConfigurationRemediationAction(
                    entity_id="sensor.temperature_missing",
                    action="review_entity_reference",
                ),
            ),
        ),
    )


def test_group_remediation_actions_handles_empty_plans() -> None:
    assert remediation_plans.group_remediation_actions(()) == ()


def test_group_remediation_actions_keeps_different_statuses_separate() -> None:
    plans = (
        remediation_plans.RemediationPlan(
            entity_id="sensor.active_reference",
            action="review_active_references",
            safety="review_required",
            reason="Entity is referenced by active configuration",
            reference_count=1,
            active_reference_count=1,
            disabled_reference_count=0,
            steps=(
                remediation_plans.RemediationStep(
                    configuration_type="automation",
                    configuration_id="automation.shared",
                    status="active",
                    action="review_entity_reference",
                ),
            ),
        ),
        remediation_plans.RemediationPlan(
            entity_id="sensor.disabled_reference",
            action="remove_disabled_references",
            safety="likely_safe",
            reason="Entity is referenced only by disabled configuration",
            reference_count=1,
            active_reference_count=0,
            disabled_reference_count=1,
            steps=(
                remediation_plans.RemediationStep(
                    configuration_type="automation",
                    configuration_id="automation.shared",
                    status="disabled",
                    action="remove_entity_reference",
                ),
            ),
        ),
    )

    groups = remediation_plans.group_remediation_actions(plans)

    assert tuple(
        (group.configuration_id, group.status)
        for group in groups
    ) == (
        ("automation.shared", "active"),
        ("automation.shared", "disabled"),
    )


def test_group_remediation_actions_preserves_plan_and_step_order() -> None:
    plans = (
        remediation_plans.RemediationPlan(
            entity_id="sensor.second",
            action="review_active_references",
            safety="review_required",
            reason="Entity is referenced by active configuration",
            reference_count=2,
            active_reference_count=2,
            disabled_reference_count=0,
            steps=(
                remediation_plans.RemediationStep(
                    configuration_type="script",
                    configuration_id="script.shared",
                    status="active",
                    action="second_action",
                ),
                remediation_plans.RemediationStep(
                    configuration_type="automation",
                    configuration_id="automation.other",
                    status="active",
                    action="review_entity_reference",
                ),
            ),
        ),
        remediation_plans.RemediationPlan(
            entity_id="sensor.first",
            action="review_active_references",
            safety="review_required",
            reason="Entity is referenced by active configuration",
            reference_count=1,
            active_reference_count=1,
            disabled_reference_count=0,
            steps=(
                remediation_plans.RemediationStep(
                    configuration_type="script",
                    configuration_id="script.shared",
                    status="active",
                    action="first_action",
                ),
            ),
        ),
    )

    groups = remediation_plans.group_remediation_actions(plans)

    assert tuple(
        (
            group.configuration_type,
            group.configuration_id,
            group.status,
        )
        for group in groups
    ) == (
        ("script", "script.shared", "active"),
        ("automation", "automation.other", "active"),
    )
    assert groups[0].actions == (
        remediation_plans.ConfigurationRemediationAction(
            entity_id="sensor.second",
            action="second_action",
        ),
        remediation_plans.ConfigurationRemediationAction(
            entity_id="sensor.first",
            action="first_action",
        ),
    )


def test_classify_remediation_plan_review_required() -> None:
    plan = remediation_plans.RemediationPlan(
        entity_id="sensor.missing",
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=1,
        active_reference_count=1,
        disabled_reference_count=0,
        steps=(),
    )

    assert remediation_plans.classify_remediation_plan(
        plan
    ) == remediation_plans.RemediationClassification(
        safety="review_required",
        confidence="high",
        reason="Entity is referenced by active configuration",
    )


def test_classify_remediation_plan_likely_safe() -> None:
    plan = remediation_plans.RemediationPlan(
        entity_id="sensor.missing",
        action="remove_disabled_references",
        safety="likely_safe",
        reason="Entity is referenced only by disabled configuration",
        reference_count=1,
        active_reference_count=0,
        disabled_reference_count=1,
        steps=(),
    )

    assert remediation_plans.classify_remediation_plan(
        plan
    ) == remediation_plans.RemediationClassification(
        safety="likely_safe",
        confidence="high",
        reason="Entity is referenced only by disabled configuration",
    )


def test_classify_remediation_plan_rejects_unknown_safety() -> None:
    plan = remediation_plans.RemediationPlan(
        entity_id="sensor.missing",
        action="unknown",
        safety="unknown",
        reason="Unknown remediation state",
        reference_count=1,
        active_reference_count=1,
        disabled_reference_count=0,
        steps=(),
    )

    try:
        remediation_plans.classify_remediation_plan(plan)
    except ValueError as err:
        assert str(err) == "Unsupported remediation safety: unknown"
    else:
        raise AssertionError("ValueError was not raised")


def test_classify_remediation_plan_preserves_plan_reason_and_safety() -> None:
    plan = remediation_plans.RemediationPlan(
        entity_id="sensor.missing",
        action="review_active_references",
        safety="review_required",
        reason="Custom remediation reason",
        reference_count=10,
        active_reference_count=0,
        disabled_reference_count=10,
        steps=(),
    )

    assert remediation_plans.classify_remediation_plan(
        plan
    ) == remediation_plans.RemediationClassification(
        safety="review_required",
        confidence="high",
        reason="Custom remediation reason",
    )


def test_preview_remediation_impact_for_removable_references() -> None:
    plan = remediation_plans.RemediationPlan(
        entity_id="sensor.missing",
        action="remove_disabled_references",
        safety="likely_safe",
        reason="Entity is referenced only by disabled configuration",
        reference_count=2,
        active_reference_count=0,
        disabled_reference_count=2,
        steps=(
            remediation_plans.RemediationStep(
                configuration_type="automation",
                configuration_id="automation.disabled_one",
                status="disabled",
                action="remove_entity_reference",
            ),
            remediation_plans.RemediationStep(
                configuration_type="script",
                configuration_id="script.disabled_two",
                status="disabled",
                action="remove_entity_reference",
            ),
        ),
    )

    assert remediation_plans.preview_remediation_impact(
        plan
    ) == remediation_plans.RemediationImpactPreview(
        entity_id="sensor.missing",
        current_reference_count=2,
        affected_configuration_count=2,
        removable_reference_count=2,
        review_reference_count=0,
        projected_reference_count=0,
    )


def test_preview_remediation_impact_for_review_references() -> None:
    plan = remediation_plans.RemediationPlan(
        entity_id="sensor.missing",
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=2,
        active_reference_count=1,
        disabled_reference_count=1,
        steps=(
            remediation_plans.RemediationStep(
                configuration_type="automation",
                configuration_id="automation.active_one",
                status="active",
                action="review_entity_reference",
            ),
            remediation_plans.RemediationStep(
                configuration_type="script",
                configuration_id="script.disabled_two",
                status="disabled",
                action="review_entity_reference",
            ),
        ),
    )

    assert remediation_plans.preview_remediation_impact(
        plan
    ) == remediation_plans.RemediationImpactPreview(
        entity_id="sensor.missing",
        current_reference_count=2,
        affected_configuration_count=2,
        removable_reference_count=0,
        review_reference_count=2,
        projected_reference_count=2,
    )


def test_preview_remediation_impact_supports_empty_plan() -> None:
    plan = remediation_plans.RemediationPlan(
        entity_id="sensor.missing",
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=0,
        active_reference_count=0,
        disabled_reference_count=0,
        steps=(),
    )

    assert remediation_plans.preview_remediation_impact(
        plan
    ) == remediation_plans.RemediationImpactPreview(
        entity_id="sensor.missing",
        current_reference_count=0,
        affected_configuration_count=0,
        removable_reference_count=0,
        review_reference_count=0,
        projected_reference_count=0,
    )


def test_preview_remediation_impact_rejects_unknown_step_action() -> None:
    plan = remediation_plans.RemediationPlan(
        entity_id="sensor.missing",
        action="unknown",
        safety="review_required",
        reason="Unknown remediation state",
        reference_count=1,
        active_reference_count=1,
        disabled_reference_count=0,
        steps=(
            remediation_plans.RemediationStep(
                configuration_type="automation",
                configuration_id="automation.one",
                status="active",
                action="unknown",
            ),
        ),
    )

    try:
        remediation_plans.preview_remediation_impact(plan)
    except ValueError as err:
        assert str(err) == "Unsupported remediation step action: unknown"
    else:
        raise AssertionError("ValueError was not raised")


def test_preview_remediation_impact_only_projects_removals() -> None:
    plan = remediation_plans.RemediationPlan(
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
                configuration_id="automation.disabled_one",
                status="disabled",
                action="remove_entity_reference",
            ),
            remediation_plans.RemediationStep(
                configuration_type="script",
                configuration_id="script.active_two",
                status="active",
                action="review_entity_reference",
            ),
        ),
    )

    assert remediation_plans.preview_remediation_impact(
        plan
    ) == remediation_plans.RemediationImpactPreview(
        entity_id="sensor.missing",
        current_reference_count=3,
        affected_configuration_count=2,
        removable_reference_count=1,
        review_reference_count=1,
        projected_reference_count=2,
    )


def test_track_remediation_progress_pending() -> None:
    original = remediation_plans.RemediationPlan(
        entity_id="sensor.missing",
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=2,
        active_reference_count=2,
        disabled_reference_count=0,
        steps=(
            remediation_plans.RemediationStep(
                configuration_type="automation",
                configuration_id="automation.one",
                status="active",
                action="review_entity_reference",
            ),
            remediation_plans.RemediationStep(
                configuration_type="script",
                configuration_id="script.two",
                status="active",
                action="review_entity_reference",
            ),
        ),
    )

    assert remediation_plans.track_remediation_progress(
        original,
        original,
    ) == remediation_plans.RemediationProgress(
        entity_id="sensor.missing",
        status="pending",
        total_action_count=2,
        completed_action_count=0,
        remaining_action_count=2,
    )


def test_track_remediation_progress_in_progress() -> None:
    original = remediation_plans.RemediationPlan(
        entity_id="sensor.missing",
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=2,
        active_reference_count=2,
        disabled_reference_count=0,
        steps=(
            remediation_plans.RemediationStep(
                configuration_type="automation",
                configuration_id="automation.one",
                status="active",
                action="review_entity_reference",
            ),
            remediation_plans.RemediationStep(
                configuration_type="script",
                configuration_id="script.two",
                status="active",
                action="review_entity_reference",
            ),
        ),
    )
    current = remediation_plans.RemediationPlan(
        entity_id="sensor.missing",
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=1,
        active_reference_count=1,
        disabled_reference_count=0,
        steps=(
            remediation_plans.RemediationStep(
                configuration_type="script",
                configuration_id="script.two",
                status="active",
                action="review_entity_reference",
            ),
        ),
    )

    assert remediation_plans.track_remediation_progress(
        original,
        current,
    ) == remediation_plans.RemediationProgress(
        entity_id="sensor.missing",
        status="in_progress",
        total_action_count=2,
        completed_action_count=1,
        remaining_action_count=1,
    )


def test_track_remediation_progress_resolved() -> None:
    original = remediation_plans.RemediationPlan(
        entity_id="sensor.missing",
        action="remove_disabled_references",
        safety="likely_safe",
        reason="Entity is referenced only by disabled configuration",
        reference_count=1,
        active_reference_count=0,
        disabled_reference_count=1,
        steps=(
            remediation_plans.RemediationStep(
                configuration_type="automation",
                configuration_id="automation.one",
                status="disabled",
                action="remove_entity_reference",
            ),
        ),
    )

    assert remediation_plans.track_remediation_progress(
        original,
        None,
    ) == remediation_plans.RemediationProgress(
        entity_id="sensor.missing",
        status="resolved",
        total_action_count=1,
        completed_action_count=1,
        remaining_action_count=0,
    )


def test_track_remediation_progress_ignores_status_and_action_changes() -> None:
    original = remediation_plans.RemediationPlan(
        entity_id="sensor.missing",
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=1,
        active_reference_count=1,
        disabled_reference_count=0,
        steps=(
            remediation_plans.RemediationStep(
                configuration_type="automation",
                configuration_id="automation.one",
                status="active",
                action="review_entity_reference",
            ),
        ),
    )
    current = remediation_plans.RemediationPlan(
        entity_id="sensor.missing",
        action="remove_disabled_references",
        safety="likely_safe",
        reason="Entity is referenced only by disabled configuration",
        reference_count=1,
        active_reference_count=0,
        disabled_reference_count=1,
        steps=(
            remediation_plans.RemediationStep(
                configuration_type="automation",
                configuration_id="automation.one",
                status="disabled",
                action="remove_entity_reference",
            ),
        ),
    )

    assert remediation_plans.track_remediation_progress(
        original,
        current,
    ) == remediation_plans.RemediationProgress(
        entity_id="sensor.missing",
        status="pending",
        total_action_count=1,
        completed_action_count=0,
        remaining_action_count=1,
    )


def test_track_remediation_progress_rejects_different_entities() -> None:
    original = remediation_plans.RemediationPlan(
        entity_id="sensor.missing",
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=1,
        active_reference_count=1,
        disabled_reference_count=0,
        steps=(),
    )
    current = remediation_plans.RemediationPlan(
        entity_id="sensor.other",
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=1,
        active_reference_count=1,
        disabled_reference_count=0,
        steps=(),
    )

    try:
        remediation_plans.track_remediation_progress(
            original,
            current,
        )
    except ValueError as err:
        assert str(err) == (
            "Cannot track remediation progress for different entities: "
            "sensor.missing != sensor.other"
        )
    else:
        raise AssertionError("ValueError was not raised")


def test_track_remediation_progress_detects_new_references() -> None:
    original = remediation_plans.RemediationPlan(
        entity_id="sensor.missing",
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=1,
        active_reference_count=1,
        disabled_reference_count=0,
        steps=(
            remediation_plans.RemediationStep(
                configuration_type="automation",
                configuration_id="automation.original",
                status="active",
                action="review_entity_reference",
            ),
        ),
    )
    current = remediation_plans.RemediationPlan(
        entity_id="sensor.missing",
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=1,
        active_reference_count=1,
        disabled_reference_count=0,
        steps=(
            remediation_plans.RemediationStep(
                configuration_type="script",
                configuration_id="script.new_reference",
                status="active",
                action="review_entity_reference",
            ),
        ),
    )

    assert remediation_plans.track_remediation_progress(
        original,
        current,
    ) == remediation_plans.RemediationProgress(
        entity_id="sensor.missing",
        status="in_progress",
        total_action_count=1,
        completed_action_count=1,
        remaining_action_count=0,
        new_reference_count=1,
    )


def test_compare_remediation_dependencies_unchanged() -> None:
    before = remediation_plans.RemediationPlan(
        entity_id="sensor.missing",
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=2,
        active_reference_count=2,
        disabled_reference_count=0,
        steps=(
            remediation_plans.RemediationStep(
                configuration_type="automation",
                configuration_id="automation.one",
                status="active",
                action="review_entity_reference",
            ),
            remediation_plans.RemediationStep(
                configuration_type="script",
                configuration_id="script.two",
                status="active",
                action="review_entity_reference",
            ),
        ),
    )

    assert remediation_plans.compare_remediation_dependencies(
        before,
        before,
    ) == remediation_plans.RemediationDependencyComparison(
        entity_id="sensor.missing",
        before_reference_count=2,
        after_reference_count=2,
        removed_reference_count=0,
        unchanged_reference_count=2,
        added_reference_count=0,
    )


def test_compare_remediation_dependencies_removed_and_added() -> None:
    before = remediation_plans.RemediationPlan(
        entity_id="sensor.missing",
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=2,
        active_reference_count=2,
        disabled_reference_count=0,
        steps=(
            remediation_plans.RemediationStep(
                configuration_type="automation",
                configuration_id="automation.old",
                status="active",
                action="review_entity_reference",
            ),
            remediation_plans.RemediationStep(
                configuration_type="script",
                configuration_id="script.keep",
                status="active",
                action="review_entity_reference",
            ),
        ),
    )
    after = remediation_plans.RemediationPlan(
        entity_id="sensor.missing",
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=2,
        active_reference_count=2,
        disabled_reference_count=0,
        steps=(
            remediation_plans.RemediationStep(
                configuration_type="script",
                configuration_id="script.keep",
                status="disabled",
                action="remove_entity_reference",
            ),
            remediation_plans.RemediationStep(
                configuration_type="scene",
                configuration_id="scene.new",
                status="active",
                action="review_entity_reference",
            ),
        ),
    )

    assert remediation_plans.compare_remediation_dependencies(
        before,
        after,
    ) == remediation_plans.RemediationDependencyComparison(
        entity_id="sensor.missing",
        before_reference_count=2,
        after_reference_count=2,
        removed_reference_count=1,
        unchanged_reference_count=1,
        added_reference_count=1,
    )


def test_compare_remediation_dependencies_resolved() -> None:
    before = remediation_plans.RemediationPlan(
        entity_id="sensor.missing",
        action="remove_disabled_references",
        safety="likely_safe",
        reason="Entity is referenced only by disabled configuration",
        reference_count=1,
        active_reference_count=0,
        disabled_reference_count=1,
        steps=(
            remediation_plans.RemediationStep(
                configuration_type="automation",
                configuration_id="automation.one",
                status="disabled",
                action="remove_entity_reference",
            ),
        ),
    )

    assert remediation_plans.compare_remediation_dependencies(
        before,
        None,
    ) == remediation_plans.RemediationDependencyComparison(
        entity_id="sensor.missing",
        before_reference_count=1,
        after_reference_count=0,
        removed_reference_count=1,
        unchanged_reference_count=0,
        added_reference_count=0,
    )


def test_compare_remediation_dependencies_rejects_different_entities() -> None:
    before = remediation_plans.RemediationPlan(
        entity_id="sensor.missing",
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=0,
        active_reference_count=0,
        disabled_reference_count=0,
        steps=(),
    )
    after = remediation_plans.RemediationPlan(
        entity_id="sensor.other",
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=0,
        active_reference_count=0,
        disabled_reference_count=0,
        steps=(),
    )

    try:
        remediation_plans.compare_remediation_dependencies(
            before,
            after,
        )
    except ValueError as err:
        assert str(err) == (
            "Cannot compare remediation dependencies for different entities: "
            "sensor.missing != sensor.other"
        )
    else:
        raise AssertionError("ValueError was not raised")


def test_compare_remediation_dependencies_deduplicates_references() -> None:
    before = remediation_plans.RemediationPlan(
        entity_id="sensor.missing",
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=2,
        active_reference_count=2,
        disabled_reference_count=0,
        steps=(
            remediation_plans.RemediationStep(
                configuration_type="automation",
                configuration_id="automation.one",
                status="active",
                action="review_entity_reference",
            ),
            remediation_plans.RemediationStep(
                configuration_type="automation",
                configuration_id="automation.one",
                status="disabled",
                action="remove_entity_reference",
            ),
        ),
    )

    assert remediation_plans.compare_remediation_dependencies(
        before,
        before,
    ) == remediation_plans.RemediationDependencyComparison(
        entity_id="sensor.missing",
        before_reference_count=1,
        after_reference_count=1,
        removed_reference_count=0,
        unchanged_reference_count=1,
        added_reference_count=0,
    )
