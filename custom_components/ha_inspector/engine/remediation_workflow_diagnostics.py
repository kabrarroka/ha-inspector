"""Remediation workflow diagnostics for HA Inspector."""

from __future__ import annotations

from typing import TypedDict

from .entities_state import EntitiesState
from .remediation_plans import (
    build_remediation_plans,
    classify_remediation_plan,
    preview_remediation_impact,
)
from .stale_reference_context import build_stale_reference_contexts


class RemediationWorkflowEntityDiagnostics(TypedDict):
    """Compact remediation diagnostics for one missing entity."""

    entity_id: str
    action: str
    safety: str
    confidence: str
    reference_count: int
    active_reference_count: int
    disabled_reference_count: int
    affected_configuration_count: int
    removable_reference_count: int
    review_reference_count: int
    projected_reference_count: int


class RemediationWorkflowDiagnostics(TypedDict):
    """Compact remediation workflow diagnostics."""

    affected_entities: int
    review_required: int
    likely_safe: int
    affected_configurations: int
    removable_references: int
    review_references: int
    entities: list[RemediationWorkflowEntityDiagnostics]


def empty_remediation_workflow_diagnostics() -> RemediationWorkflowDiagnostics:
    """Return an empty remediation workflow summary."""
    return {
        "affected_entities": 0,
        "review_required": 0,
        "likely_safe": 0,
        "affected_configurations": 0,
        "removable_references": 0,
        "review_references": 0,
        "entities": [],
    }


def remediation_workflow_diagnostics(
    entities: EntitiesState,
) -> RemediationWorkflowDiagnostics:
    """Build remediation workflow diagnostics for missing entity references."""
    if not entities.missing_entities:
        return empty_remediation_workflow_diagnostics()

    disabled_automation_ids = {
        automation.entity_id
        for automation in entities.disabled_automations
    }

    contexts = build_stale_reference_contexts(
        entities.missing_entities,
        (
            (
                dependency.entity_id,
                dependency.referenced_entities,
                dependency.entity_id in disabled_automation_ids,
            )
            for dependency in entities.automation_dependencies
        ),
        (
            (
                dependency.entity_id,
                dependency.referenced_entities,
                False,
            )
            for dependency in entities.script_dependencies
        ),
        (
            (
                dependency.entity_id,
                dependency.referenced_entities,
                False,
            )
            for dependency in entities.scene_dependencies
        ),
    )

    plans = build_remediation_plans(contexts)

    entity_diagnostics: list[RemediationWorkflowEntityDiagnostics] = []
    review_required = 0
    likely_safe = 0
    removable_references = 0
    review_references = 0
    affected_configurations: set[tuple[str, str]] = set()

    for plan in plans:
        classification = classify_remediation_plan(plan)
        preview = preview_remediation_impact(plan)

        if classification.safety == "review_required":
            review_required += 1
        elif classification.safety == "likely_safe":
            likely_safe += 1

        removable_references += preview.removable_reference_count
        review_references += preview.review_reference_count

        affected_configurations.update(
            (
                step.configuration_type,
                step.configuration_id,
            )
            for step in plan.steps
        )

        entity_diagnostics.append(
            {
                "entity_id": plan.entity_id,
                "action": plan.action,
                "safety": classification.safety,
                "confidence": classification.confidence,
                "reference_count": plan.reference_count,
                "active_reference_count": plan.active_reference_count,
                "disabled_reference_count": plan.disabled_reference_count,
                "affected_configuration_count": (
                    preview.affected_configuration_count
                ),
                "removable_reference_count": (
                    preview.removable_reference_count
                ),
                "review_reference_count": preview.review_reference_count,
                "projected_reference_count": (
                    preview.projected_reference_count
                ),
            }
        )

    entity_diagnostics.sort(key=lambda item: item["entity_id"])

    return {
        "affected_entities": len(entity_diagnostics),
        "review_required": review_required,
        "likely_safe": likely_safe,
        "affected_configurations": len(affected_configurations),
        "removable_references": removable_references,
        "review_references": review_references,
        "entities": entity_diagnostics,
    }


__all__ = [
    "RemediationWorkflowDiagnostics",
    "RemediationWorkflowEntityDiagnostics",
    "empty_remediation_workflow_diagnostics",
    "remediation_workflow_diagnostics",
]
