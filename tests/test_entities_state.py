from custom_components.ha_inspector.engine.entities_state import (
    AutomationDependencySummary,
    DependencyHealthSummary,
    DisabledAutomation,
    DuplicateEntityName,
    EntitiesState,
    EntityDependencySummary,
    EntitySummary,
    SceneDependencySummary,
    ScriptDependencySummary,
)


def test_entities_state_defaults() -> None:
    state = EntitiesState()

    assert state.as_dict() == {
        "total_entities": 0,
        "domain_counts": {},
        "unavailable_count": 0,
        "unknown_count": 0,
        "unavailable_domains": {},
        "unknown_domains": {},
        "unavailable_entities": [],
        "unknown_entities": [],
        "duplicate_name_count": 0,
        "duplicate_names": [],
        "disabled_automation_count": 0,
        "disabled_automations": [],
        "automation_dependency_count": 0,
        "automation_dependencies": [],
        "script_dependency_count": 0,
        "script_dependencies": [],
        "scene_dependency_count": 0,
        "scene_dependencies": [],
        "entity_dependency_count": 0,
        "entity_dependencies": [],
        "unavailable_dependency_count": 0,
        "unavailable_dependencies": [],
        "unknown_dependency_count": 0,
        "unknown_dependencies": [],
        "unreferenced_entity_count": 0,
        "unreferenced_entities": [],
        "missing_entity_count": 0,
        "missing_entities": [],
        "unassigned_area_count": 0,
        "unassigned_area_entities": [],
    }


def test_entities_state_nested_values() -> None:
    state = EntitiesState(
        total_entities=3,
        domain_counts={"sensor": 2, "automation": 1},
        unavailable_count=1,
        unavailable_domains={"sensor": 1},
        unavailable_entities=[
            EntitySummary(
                entity_id="sensor.temperature",
                name="Temperature",
                domain="sensor",
            )
        ],
        duplicate_name_count=1,
        duplicate_names=[
            DuplicateEntityName(
                name="Temperature",
                entity_ids=[
                    "sensor.kitchen_temperature",
                    "sensor.living_room_temperature",
                ],
                count=2,
            )
        ],
        disabled_automation_count=1,
        disabled_automations=[
            DisabledAutomation(
                entity_id="automation.old_rule",
                name="Old rule",
                disabled_by="user",
            )
        ],
        automation_dependency_count=1,
        automation_dependencies=[
            AutomationDependencySummary(
                entity_id="automation.kitchen",
                name="Kitchen",
                referenced_entities=[
                    "binary_sensor.motion",
                    "light.kitchen",
                ],
                referenced_entity_count=2,
            )
        ],
        script_dependency_count=1,
        script_dependencies=[
            ScriptDependencySummary(
                entity_id="script.evening",
                name="Evening",
                referenced_entities=[
                    "light.living_room",
                    "media_player.tv",
                ],
                referenced_entity_count=2,
            )
        ],
        scene_dependency_count=1,
        scene_dependencies=[
            SceneDependencySummary(
                entity_id="scene.movie",
                name="Movie",
                referenced_entities=[
                    "light.living_room",
                    "media_player.tv",
                ],
                referenced_entity_count=2,
            )
        ],
        entity_dependency_count=1,
        entity_dependencies=[
            EntityDependencySummary(
                entity_id="light.living_room",
                reference_count=3,
                automation_references=["automation.evening"],
                script_references=["script.evening"],
                scene_references=["scene.movie"],
            )
        ],
        unavailable_dependency_count=1,
        unavailable_dependencies=[
            DependencyHealthSummary(
                entity_id="sensor.temperature",
                name="Temperature",
                domain="sensor",
                state="unavailable",
                reference_count=2,
                automation_references=["automation.climate"],
                script_references=["script.climate"],
                scene_references=[],
            )
        ],
        unknown_dependency_count=1,
        unknown_dependencies=[
            DependencyHealthSummary(
                entity_id="sensor.humidity",
                name="Humidity",
                domain="sensor",
                state="unknown",
                reference_count=1,
                automation_references=["automation.humidity"],
                script_references=[],
                scene_references=[],
            )
        ],
        missing_entity_count=2,
        missing_entities=[
            "sensor.missing",
            "switch.missing",
        ],
    )

    assert state.as_dict() == {
        "total_entities": 3,
        "domain_counts": {
            "sensor": 2,
            "automation": 1,
        },
        "unavailable_count": 1,
        "unknown_count": 0,
        "unavailable_domains": {
            "sensor": 1,
        },
        "unknown_domains": {},
        "unavailable_entities": [
            {
                "entity_id": "sensor.temperature",
                "name": "Temperature",
                "domain": "sensor",
            }
        ],
        "unknown_entities": [],
        "duplicate_name_count": 1,
        "duplicate_names": [
            {
                "name": "Temperature",
                "entity_ids": [
                    "sensor.kitchen_temperature",
                    "sensor.living_room_temperature",
                ],
                "count": 2,
            }
        ],
        "disabled_automation_count": 1,
        "disabled_automations": [
            {
                "entity_id": "automation.old_rule",
                "name": "Old rule",
                "disabled_by": "user",
            }
        ],
        "automation_dependency_count": 1,
        "automation_dependencies": [
            {
                "entity_id": "automation.kitchen",
                "name": "Kitchen",
                "referenced_entities": [
                    "binary_sensor.motion",
                    "light.kitchen",
                ],
                "referenced_entity_count": 2,
            }
        ],
        "script_dependency_count": 1,
        "script_dependencies": [
            {
                "entity_id": "script.evening",
                "name": "Evening",
                "referenced_entities": [
                    "light.living_room",
                    "media_player.tv",
                ],
                "referenced_entity_count": 2,
            }
        ],
        "scene_dependency_count": 1,
        "scene_dependencies": [
            {
                "entity_id": "scene.movie",
                "name": "Movie",
                "referenced_entities": [
                    "light.living_room",
                    "media_player.tv",
                ],
                "referenced_entity_count": 2,
            }
        ],
        "entity_dependency_count": 1,
        "entity_dependencies": [
            {
                "entity_id": "light.living_room",
                "reference_count": 3,
                "automation_references": ["automation.evening"],
                "script_references": ["script.evening"],
                "scene_references": ["scene.movie"],
            }
        ],
        "unavailable_dependency_count": 1,
        "unavailable_dependencies": [
            {
                "entity_id": "sensor.temperature",
                "name": "Temperature",
                "domain": "sensor",
                "state": "unavailable",
                "reference_count": 2,
                "automation_references": ["automation.climate"],
                "script_references": ["script.climate"],
                "scene_references": [],
            }
        ],
        "unknown_dependency_count": 1,
        "unknown_dependencies": [
            {
                "entity_id": "sensor.humidity",
                "name": "Humidity",
                "domain": "sensor",
                "state": "unknown",
                "reference_count": 1,
                "automation_references": ["automation.humidity"],
                "script_references": [],
                "scene_references": [],
            }
        ],
        "unreferenced_entity_count": 0,
        "unreferenced_entities": [],
        "missing_entity_count": 2,
        "missing_entities": [
            "sensor.missing",
            "switch.missing",
        ],
        "unassigned_area_count": 0,
        "unassigned_area_entities": [],

    }
