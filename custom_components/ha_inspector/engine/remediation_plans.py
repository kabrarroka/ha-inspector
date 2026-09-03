"""Per-entity dependency remediation plan helpers for HA Inspector."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .cleanup_recommendations import build_cleanup_recommendation
from .entity_dependency_impact_summary import (
    build_entity_dependency_impact_summary,
)
from .stale_reference_context import StaleReferenceContext


@dataclass(frozen=True, slots=True)
class RemediationStep:
    """Represent one configuration review step for a stale entity reference."""

    configuration_type: str
    configuration_id: str
    status: str
    action: str


@dataclass(frozen=True, slots=True)
class RemediationPlan:
    """Represent a non-destructive remediation plan for one entity."""

    entity_id: str
    action: str
    safety: str
    reason: str
    reference_count: int
    active_reference_count: int
    disabled_reference_count: int
    steps: tuple[RemediationStep, ...]


def _build_steps(
    context: StaleReferenceContext,
    action: str,
) -> tuple[RemediationStep, ...]:
    """Build remediation steps in stable configuration-type order."""
    steps: list[RemediationStep] = []

    references = (
        (
            "automation",
            "active",
            context.active_automation_references,
        ),
        (
            "automation",
            "disabled",
            context.disabled_automation_references,
        ),
        (
            "script",
            "active",
            context.active_script_references,
        ),
        (
            "script",
            "disabled",
            context.disabled_script_references,
        ),
        (
            "scene",
            "active",
            context.active_scene_references,
        ),
        (
            "scene",
            "disabled",
            context.disabled_scene_references,
        ),
    )

    for configuration_type, status, configuration_ids in references:
        for configuration_id in configuration_ids:
            steps.append(
                RemediationStep(
                    configuration_type=configuration_type,
                    configuration_id=configuration_id,
                    status=status,
                    action=action,
                )
            )

    return tuple(steps)


def build_remediation_plan(
    context: StaleReferenceContext,
) -> RemediationPlan | None:
    """Build one non-destructive remediation plan for a stale entity."""
    recommendation = build_cleanup_recommendation(context)
    if recommendation is None:
        return None

    impact = build_entity_dependency_impact_summary(context)

    return RemediationPlan(
        entity_id=context.entity_id,
        action=recommendation.action,
        safety=recommendation.safety,
        reason=recommendation.reason,
        reference_count=impact.reference_count,
        active_reference_count=impact.active_reference_count,
        disabled_reference_count=impact.disabled_reference_count,
        steps=_build_steps(
            context,
            (
                "remove_entity_reference"
                if recommendation.action == "remove_disabled_references"
                else "review_entity_reference"
            ),
        ),
    )


def build_remediation_plans(
    contexts: Iterable[StaleReferenceContext],
) -> tuple[RemediationPlan, ...]:
    """Build remediation plans, skipping contexts with no recommendation."""
    plans = (
        build_remediation_plan(context)
        for context in contexts
    )

    return tuple(
        plan
        for plan in plans
        if plan is not None
    )
