"""Tests for safe dependency cleanup recommendations."""

from custom_components.ha_inspector.engine import cleanup_recommendations
from custom_components.ha_inspector.engine.stale_reference_context import (
    StaleReferenceContext,
)


def _context(
    *,
    entity_id: str = "sensor.missing",
    active_automations: tuple[str, ...] = (),
    disabled_automations: tuple[str, ...] = (),
    active_scripts: tuple[str, ...] = (),
    disabled_scripts: tuple[str, ...] = (),
    active_scenes: tuple[str, ...] = (),
    disabled_scenes: tuple[str, ...] = (),
) -> StaleReferenceContext:
    return StaleReferenceContext(
        entity_id=entity_id,
        active_automation_references=active_automations,
        disabled_automation_references=disabled_automations,
        active_script_references=active_scripts,
        disabled_script_references=disabled_scripts,
        active_scene_references=active_scenes,
        disabled_scene_references=disabled_scenes,
    )


def test_active_references_require_review() -> None:
    context = _context(
        active_automations=("automation.second", "automation.first"),
        disabled_scripts=("script.disabled",),
        active_scenes=("scene.active",),
    )

    recommendation = (
        cleanup_recommendations.build_cleanup_recommendation(context)
    )

    assert recommendation == cleanup_recommendations.CleanupRecommendation(
        entity_id="sensor.missing",
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        affected_configurations=(
            "automation.first",
            "automation.second",
            "scene.active",
            "script.disabled",
        ),
    )


def test_only_disabled_references_are_likely_safe_to_remove() -> None:
    context = _context(
        disabled_automations=("automation.disabled",),
        disabled_scripts=("script.disabled",),
        disabled_scenes=("scene.disabled",),
    )

    recommendation = (
        cleanup_recommendations.build_cleanup_recommendation(context)
    )

    assert recommendation == cleanup_recommendations.CleanupRecommendation(
        entity_id="sensor.missing",
        action="remove_disabled_references",
        safety="likely_safe",
        reason="Entity is referenced only by disabled configuration",
        affected_configurations=(
            "automation.disabled",
            "scene.disabled",
            "script.disabled",
        ),
    )


def test_no_references_produce_no_recommendation() -> None:
    assert (
        cleanup_recommendations.build_cleanup_recommendation(_context())
        is None
    )


def test_affected_configurations_are_unique() -> None:
    context = _context(
        active_automations=("automation.shared",),
        active_scripts=("automation.shared",),
        disabled_scenes=("scene.disabled",),
    )

    recommendation = (
        cleanup_recommendations.build_cleanup_recommendation(context)
    )

    assert recommendation is not None
    assert recommendation.affected_configurations == (
        "automation.shared",
        "scene.disabled",
    )


def test_build_cleanup_recommendations_skips_empty_contexts() -> None:
    contexts = (
        _context(entity_id="sensor.unused"),
        _context(
            entity_id="sensor.active",
            active_scripts=("script.active",),
        ),
        _context(
            entity_id="sensor.disabled",
            disabled_automations=("automation.disabled",),
        ),
    )

    recommendations = (
        cleanup_recommendations.build_cleanup_recommendations(contexts)
    )

    assert tuple(
        recommendation.entity_id for recommendation in recommendations
    ) == (
        "sensor.active",
        "sensor.disabled",
    )
