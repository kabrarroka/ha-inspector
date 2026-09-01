"""Safe dependency cleanup recommendation helpers for HA Inspector."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .stale_reference_context import StaleReferenceContext


@dataclass(frozen=True, slots=True)
class CleanupRecommendation:
    """Represent one non-destructive dependency cleanup recommendation."""

    entity_id: str
    action: str
    safety: str
    reason: str
    affected_configurations: tuple[str, ...]


def _affected_configurations(
    context: StaleReferenceContext,
) -> tuple[str, ...]:
    """Return all affected configurations in stable order."""
    return tuple(
        sorted(
            {
                *context.active_automation_references,
                *context.disabled_automation_references,
                *context.active_script_references,
                *context.disabled_script_references,
                *context.active_scene_references,
                *context.disabled_scene_references,
            }
        )
    )


def build_cleanup_recommendation(
    context: StaleReferenceContext,
) -> CleanupRecommendation | None:
    """Build one safe cleanup recommendation from stale reference context."""
    active_references = (
        context.active_automation_references
        + context.active_script_references
        + context.active_scene_references
    )
    disabled_references = (
        context.disabled_automation_references
        + context.disabled_script_references
        + context.disabled_scene_references
    )

    if active_references:
        return CleanupRecommendation(
            entity_id=context.entity_id,
            action="review_active_references",
            safety="review_required",
            reason="Entity is referenced by active configuration",
            affected_configurations=_affected_configurations(context),
        )

    if disabled_references:
        return CleanupRecommendation(
            entity_id=context.entity_id,
            action="remove_disabled_references",
            safety="likely_safe",
            reason="Entity is referenced only by disabled configuration",
            affected_configurations=_affected_configurations(context),
        )

    return None


def build_cleanup_recommendations(
    contexts: Iterable[StaleReferenceContext],
) -> tuple[CleanupRecommendation, ...]:
    """Build cleanup recommendations, skipping contexts with no references."""
    recommendations = (
        build_cleanup_recommendation(context)
        for context in contexts
    )

    return tuple(
        recommendation
        for recommendation in recommendations
        if recommendation is not None
    )
