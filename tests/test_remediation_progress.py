"""Tests for cross-inspection remediation progress."""

from __future__ import annotations

from custom_components.ha_inspector.engine.remediation_plans import (
    RemediationPlan,
    RemediationStep,
)
from custom_components.ha_inspector.engine.remediation_progress import (
    build_remediation_progress,
)


def _plan(
    entity_id: str,
    *configuration_ids: str,
) -> RemediationPlan:
    """Build a representative remediation plan."""
    return RemediationPlan(
        entity_id=entity_id,
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=len(configuration_ids),
        active_reference_count=len(configuration_ids),
        disabled_reference_count=0,
        steps=tuple(
            RemediationStep(
                configuration_type="automation",
                configuration_id=configuration_id,
                status="active",
                action="review_entity_reference",
            )
            for configuration_id in configuration_ids
        ),
    )


def test_progress_without_baselines_identifies_new_plans() -> None:
    """Current remediation plans without baselines are returned for capture."""
    current = (
        _plan("sensor.one", "automation.one"),
        _plan("sensor.two", "automation.two"),
    )

    result = build_remediation_progress({}, current)

    assert result.progress == ()
    assert result.new_baselines == current


def test_progress_tracks_existing_baseline_without_replacing_it() -> None:
    """Existing baselines are compared with the current remediation plan."""
    baseline = _plan(
        "sensor.missing",
        "automation.one",
        "automation.two",
    )
    current = _plan(
        "sensor.missing",
        "automation.two",
    )

    result = build_remediation_progress(
        {"sensor.missing": baseline},
        (current,),
    )

    assert result.new_baselines == ()
    assert len(result.progress) == 1

    progress = result.progress[0]
    assert progress.entity_id == "sensor.missing"
    assert progress.status == "in_progress"
    assert progress.total_action_count == 2
    assert progress.completed_action_count == 1
    assert progress.remaining_action_count == 1
    assert progress.new_reference_count == 0


def test_progress_marks_missing_current_plan_as_resolved() -> None:
    """A persisted baseline with no current plan is resolved."""
    baseline = _plan(
        "sensor.missing",
        "automation.one",
    )

    result = build_remediation_progress(
        {"sensor.missing": baseline},
        (),
    )

    assert result.new_baselines == ()
    assert len(result.progress) == 1

    progress = result.progress[0]
    assert progress.entity_id == "sensor.missing"
    assert progress.status == "resolved"
    assert progress.total_action_count == 1
    assert progress.completed_action_count == 1
    assert progress.remaining_action_count == 0
    assert progress.new_reference_count == 0


def test_progress_detects_reference_added_after_baseline() -> None:
    """References introduced after the baseline are reported as new."""
    baseline = _plan(
        "sensor.missing",
        "automation.one",
    )
    current = _plan(
        "sensor.missing",
        "automation.one",
        "automation.two",
    )

    result = build_remediation_progress(
        {"sensor.missing": baseline},
        (current,),
    )

    assert result.new_baselines == ()
    assert len(result.progress) == 1

    progress = result.progress[0]
    assert progress.status == "in_progress"
    assert progress.total_action_count == 1
    assert progress.completed_action_count == 0
    assert progress.remaining_action_count == 1
    assert progress.new_reference_count == 1


def test_progress_orders_entities_stably() -> None:
    """Progress and new baselines use stable entity-id ordering."""
    baselines = {
        "sensor.zeta": _plan("sensor.zeta", "automation.zeta"),
        "sensor.alpha": _plan("sensor.alpha", "automation.alpha"),
    }
    current = (
        _plan("sensor.zeta", "automation.zeta"),
        _plan("sensor.new_zeta", "automation.new_zeta"),
        _plan("sensor.alpha", "automation.alpha"),
        _plan("sensor.new_alpha", "automation.new_alpha"),
    )

    result = build_remediation_progress(baselines, current)

    assert tuple(item.entity_id for item in result.progress) == (
        "sensor.alpha",
        "sensor.zeta",
    )
    assert tuple(item.entity_id for item in result.new_baselines) == (
        "sensor.new_alpha",
        "sensor.new_zeta",
    )


def test_progress_diagnostics_summarizes_entity_progress() -> None:
    """Progress diagnostics summarize cross-inspection remediation state."""
    from custom_components.ha_inspector.engine.remediation_plans import (
        RemediationProgress,
    )
    from custom_components.ha_inspector.engine.remediation_progress import (
        remediation_progress_diagnostics,
    )

    progress = (
        RemediationProgress(
            entity_id="sensor.pending",
            status="pending",
            total_action_count=2,
            completed_action_count=0,
            remaining_action_count=2,
        ),
        RemediationProgress(
            entity_id="sensor.active",
            status="in_progress",
            total_action_count=3,
            completed_action_count=1,
            remaining_action_count=2,
            new_reference_count=1,
        ),
        RemediationProgress(
            entity_id="sensor.resolved",
            status="resolved",
            total_action_count=1,
            completed_action_count=1,
            remaining_action_count=0,
        ),
    )

    diagnostics = remediation_progress_diagnostics(progress)

    assert diagnostics == {
        "tracked_entities": 3,
        "pending": 1,
        "in_progress": 1,
        "resolved": 1,
        "total_actions": 6,
        "completed_actions": 2,
        "remaining_actions": 4,
        "new_references": 1,
        "entities": [
            {
                "entity_id": "sensor.active",
                "status": "in_progress",
                "total_action_count": 3,
                "completed_action_count": 1,
                "remaining_action_count": 2,
                "new_reference_count": 1,
            },
            {
                "entity_id": "sensor.pending",
                "status": "pending",
                "total_action_count": 2,
                "completed_action_count": 0,
                "remaining_action_count": 2,
                "new_reference_count": 0,
            },
            {
                "entity_id": "sensor.resolved",
                "status": "resolved",
                "total_action_count": 1,
                "completed_action_count": 1,
                "remaining_action_count": 0,
                "new_reference_count": 0,
            },
        ],
    }


def test_empty_progress_diagnostics() -> None:
    """Empty progress has a stable diagnostics document."""
    from custom_components.ha_inspector.engine.remediation_progress import (
        remediation_progress_diagnostics,
    )

    assert remediation_progress_diagnostics(()) == {
        "tracked_entities": 0,
        "pending": 0,
        "in_progress": 0,
        "resolved": 0,
        "total_actions": 0,
        "completed_actions": 0,
        "remaining_actions": 0,
        "new_references": 0,
        "entities": [],
    }
