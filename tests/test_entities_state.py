from custom_components.ha_inspector.engine.entities_state import (
    AutomationDependencySummary,
    DisabledAutomation,
    DuplicateEntityName,
    EntitiesState,
    EntitySummary,
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
        "unassigned_area_count": 0,
        "unassigned_area_entities": [],

    }
