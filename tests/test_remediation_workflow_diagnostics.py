"""Tests for remediation workflow diagnostics."""

from custom_components.ha_inspector.engine.entities_state import (
    AutomationDependencySummary,
    DisabledAutomation,
    EntitiesState,
    SceneDependencySummary,
    ScriptDependencySummary,
)
from custom_components.ha_inspector.engine.remediation_workflow_diagnostics import (
    remediation_workflow_diagnostics,
)


def test_remediation_workflow_diagnostics_for_empty_state() -> None:
    """Empty entity state exposes zeroed remediation diagnostics."""
    assert remediation_workflow_diagnostics(EntitiesState()) == {
        "affected_entities": 0,
        "review_required": 0,
        "likely_safe": 0,
        "affected_configurations": 0,
        "removable_references": 0,
        "review_references": 0,
        "entities": [],
    }


def test_remediation_workflow_diagnostics_for_mixed_references() -> None:
    """Missing entities expose remediation classification and impact."""
    entities = EntitiesState(
        missing_entity_count=2,
        missing_entities=[
            "sensor.missing_mixed",
            "sensor.missing_disabled",
        ],
        disabled_automation_count=2,
        disabled_automations=[
            DisabledAutomation(
                entity_id="automation.disabled_mixed",
                name="Disabled mixed",
                disabled_by="user",
            ),
            DisabledAutomation(
                entity_id="automation.disabled_only",
                name="Disabled only",
                disabled_by="user",
            ),
        ],
        automation_dependencies=[
            AutomationDependencySummary(
                entity_id="automation.active",
                name="Active",
                referenced_entities=["sensor.missing_mixed"],
                referenced_entity_count=1,
            ),
            AutomationDependencySummary(
                entity_id="automation.disabled_mixed",
                name="Disabled mixed",
                referenced_entities=["sensor.missing_mixed"],
                referenced_entity_count=1,
            ),
            AutomationDependencySummary(
                entity_id="automation.disabled_only",
                name="Disabled only",
                referenced_entities=["sensor.missing_disabled"],
                referenced_entity_count=1,
            ),
        ],
        script_dependencies=[
            ScriptDependencySummary(
                entity_id="script.active",
                name="Active script",
                referenced_entities=["sensor.missing_mixed"],
                referenced_entity_count=1,
            ),
        ],
        scene_dependencies=[
            SceneDependencySummary(
                entity_id="scene.active",
                name="Active scene",
                referenced_entities=["sensor.missing_mixed"],
                referenced_entity_count=1,
            ),
        ],
    )

    assert remediation_workflow_diagnostics(entities) == {
        "affected_entities": 2,
        "review_required": 1,
        "likely_safe": 1,
        "affected_configurations": 5,
        "removable_references": 1,
        "review_references": 4,
        "entities": [
            {
                "entity_id": "sensor.missing_disabled",
                "action": "remove_disabled_references",
                "safety": "likely_safe",
                "confidence": "high",
                "reference_count": 1,
                "active_reference_count": 0,
                "disabled_reference_count": 1,
                "affected_configuration_count": 1,
                "removable_reference_count": 1,
                "review_reference_count": 0,
                "projected_reference_count": 0,
            },
            {
                "entity_id": "sensor.missing_mixed",
                "action": "review_active_references",
                "safety": "review_required",
                "confidence": "high",
                "reference_count": 4,
                "active_reference_count": 3,
                "disabled_reference_count": 1,
                "affected_configuration_count": 4,
                "removable_reference_count": 0,
                "review_reference_count": 4,
                "projected_reference_count": 4,
            },
        ],
    }


def test_remediation_workflow_diagnostics_ignores_existing_entities() -> None:
    """Only missing referenced entities participate in remediation workflow."""
    entities = EntitiesState(
        automation_dependencies=[
            AutomationDependencySummary(
                entity_id="automation.active",
                name="Active",
                referenced_entities=["sensor.existing"],
                referenced_entity_count=1,
            ),
        ],
    )

    assert remediation_workflow_diagnostics(entities) == {
        "affected_entities": 0,
        "review_required": 0,
        "likely_safe": 0,
        "affected_configurations": 0,
        "removable_references": 0,
        "review_references": 0,
        "entities": [],
    }


def test_remediation_workflow_diagnostics_deduplicates_configurations() -> None:
    """Shared configurations are counted once in the workflow summary."""
    entities = EntitiesState(
        missing_entity_count=2,
        missing_entities=[
            "sensor.missing_one",
            "sensor.missing_two",
        ],
        automation_dependencies=[
            AutomationDependencySummary(
                entity_id="automation.shared",
                name="Shared",
                referenced_entities=[
                    "sensor.missing_one",
                    "sensor.missing_two",
                ],
                referenced_entity_count=2,
            ),
        ],
    )

    diagnostics = remediation_workflow_diagnostics(entities)

    assert diagnostics["affected_entities"] == 2
    assert diagnostics["review_required"] == 2
    assert diagnostics["likely_safe"] == 0
    assert diagnostics["affected_configurations"] == 1
    assert diagnostics["removable_references"] == 0
    assert diagnostics["review_references"] == 2


def test_remediation_workflow_diagnostics_skips_missing_without_references() -> None:
    """Missing entities without dependency references require no remediation."""
    entities = EntitiesState(
        missing_entity_count=1,
        missing_entities=["sensor.missing"],
    )

    assert remediation_workflow_diagnostics(entities) == {
        "affected_entities": 0,
        "review_required": 0,
        "likely_safe": 0,
        "affected_configurations": 0,
        "removable_references": 0,
        "review_references": 0,
        "entities": [],
    }
