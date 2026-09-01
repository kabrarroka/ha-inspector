"""Per-entity dependency impact summary helpers for HA Inspector."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .stale_reference_context import StaleReferenceContext


@dataclass(frozen=True, slots=True)
class EntityDependencyImpactSummary:
    """Represent configuration impact for one referenced entity."""

    entity_id: str
    reference_count: int
    active_reference_count: int
    disabled_reference_count: int
    automation_reference_count: int
    script_reference_count: int
    scene_reference_count: int


def build_entity_dependency_impact_summary(
    context: StaleReferenceContext,
) -> EntityDependencyImpactSummary:
    """Build the dependency impact summary for one entity."""
    active_automation_count = len(context.active_automation_references)
    disabled_automation_count = len(
        context.disabled_automation_references
    )
    active_script_count = len(context.active_script_references)
    disabled_script_count = len(context.disabled_script_references)
    active_scene_count = len(context.active_scene_references)
    disabled_scene_count = len(context.disabled_scene_references)

    active_reference_count = (
        active_automation_count
        + active_script_count
        + active_scene_count
    )
    disabled_reference_count = (
        disabled_automation_count
        + disabled_script_count
        + disabled_scene_count
    )

    return EntityDependencyImpactSummary(
        entity_id=context.entity_id,
        reference_count=(
            active_reference_count + disabled_reference_count
        ),
        active_reference_count=active_reference_count,
        disabled_reference_count=disabled_reference_count,
        automation_reference_count=(
            active_automation_count + disabled_automation_count
        ),
        script_reference_count=(
            active_script_count + disabled_script_count
        ),
        scene_reference_count=(
            active_scene_count + disabled_scene_count
        ),
    )


def build_entity_dependency_impact_summaries(
    contexts: Iterable[StaleReferenceContext],
) -> tuple[EntityDependencyImpactSummary, ...]:
    """Build dependency impact summaries for referenced entities."""
    return tuple(
        build_entity_dependency_impact_summary(context)
        for context in contexts
    )
