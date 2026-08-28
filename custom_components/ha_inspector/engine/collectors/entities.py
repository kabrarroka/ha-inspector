"""Entity state and registry collector for HA Inspector."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import TYPE_CHECKING

from homeassistant.components.automation import entities_in_automation
from homeassistant.components.homeassistant.scene import entities_in_scene
from homeassistant.components.script import entities_in_script
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from ..automation_dependencies import automation_dependency_from_entities
from ..context import InspectionContext
from ..entities_state import (
    AutomationDependencySummary,
    DisabledAutomation,
    DuplicateEntityName,
    EntitiesState,
    EntitySummary,
    SceneDependencySummary,
    ScriptDependencySummary,
)
from ..scene_dependencies import scene_dependency_from_entities
from ..script_dependencies import script_dependency_from_entities
from .base import BaseCollector

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class EntitiesCollector(BaseCollector):
    """Collect entity state and registry statistics."""

    collector_id = "entities"

    async def collect(
        self,
        hass: HomeAssistant,
        context: InspectionContext,
    ) -> None:
        """Collect entity state, duplicate-name and disabled-automation data."""
        states = hass.states.async_all()

        domain_counts: Counter[str] = Counter()
        unavailable_domains: Counter[str] = Counter()
        unknown_domains: Counter[str] = Counter()

        unavailable_entities: list[EntitySummary] = []
        unknown_entities: list[EntitySummary] = []
        entities_by_name: defaultdict[str, list[str]] = defaultdict(list)

        for state in states:
            domain = state.domain
            domain_counts[domain] += 1

            entity_summary = EntitySummary(
                entity_id=state.entity_id,
                name=state.name,
                domain=domain,
            )

            normalized_name = state.name.strip().casefold()
            if normalized_name:
                entities_by_name[normalized_name].append(state.entity_id)

            if state.state == STATE_UNAVAILABLE:
                unavailable_domains[domain] += 1
                unavailable_entities.append(entity_summary)
            elif state.state == STATE_UNKNOWN:
                unknown_domains[domain] += 1
                unknown_entities.append(entity_summary)

        duplicate_names = [
            DuplicateEntityName(
                name=next(
                    (
                        state.name
                        for state in states
                        if state.entity_id == entity_ids[0]
                    ),
                    normalized_name,
                ),
                entity_ids=sorted(entity_ids),
                count=len(entity_ids),
            )
            for normalized_name, entity_ids in sorted(entities_by_name.items())
            if len(entity_ids) > 1
        ]

        registry = er.async_get(hass)
        device_registry = dr.async_get(hass)

        unassigned_area_entities: list[EntitySummary] = []

        for entry in registry.entities.values():
            if entry.entity_category is not None:
                continue

            if entry.area_id is not None:
                continue

            if entry.device_id is not None:
                device = device_registry.async_get(entry.device_id)

                if device is not None and device.area_id is not None:
                    continue

            state = hass.states.get(entry.entity_id)
            name = (
                state.name
                if state is not None
                else entry.name or entry.original_name or entry.entity_id
            )

            unassigned_area_entities.append(
                EntitySummary(
                    entity_id=entry.entity_id,
                    name=name,
                    domain=entry.domain,
                )
            )

        unassigned_area_entities.sort(key=lambda item: item.entity_id)
        disabled_automations = [
            DisabledAutomation(
                entity_id=entry.entity_id,
                name=entry.name or entry.original_name or entry.entity_id,
                disabled_by=(
                    entry.disabled_by.value
                    if hasattr(entry.disabled_by, "value")
                    else str(entry.disabled_by)
                ),
            )
            for entry in registry.entities.values()
            if entry.domain == "automation" and entry.disabled_by is not None
        ]
        disabled_automations.sort(key=lambda item: item.entity_id)

        automation_dependencies: list[AutomationDependencySummary] = []

        for entry in registry.entities.values():
            if entry.domain != "automation":
                continue

            name = entry.name or entry.original_name or entry.entity_id

            automation_dependency = automation_dependency_from_entities(
                entry.entity_id,
                name,
                entities_in_automation(hass, entry.entity_id),
            )

            automation_dependencies.append(
                AutomationDependencySummary(
                    entity_id=automation_dependency.automation_entity_id,
                    name=automation_dependency.name,
                    referenced_entities=list(
                        automation_dependency.referenced_entities
                    ),
                    referenced_entity_count=(
                        automation_dependency.referenced_entity_count
                    ),
                )
            )

        automation_dependencies.sort(
            key=lambda item: item.entity_id
        )

        script_dependencies: list[ScriptDependencySummary] = []

        for entry in registry.entities.values():
            if entry.domain != "script":
                continue

            name = entry.name or entry.original_name or entry.entity_id

            script_dependency = script_dependency_from_entities(
                entry.entity_id,
                name,
                entities_in_script(hass, entry.entity_id),
            )

            script_dependencies.append(
                ScriptDependencySummary(
                    entity_id=script_dependency.script_entity_id,
                    name=script_dependency.name,
                    referenced_entities=list(
                        script_dependency.referenced_entities
                    ),
                    referenced_entity_count=(
                        script_dependency.referenced_entity_count
                    ),
                )
            )

        script_dependencies.sort(
            key=lambda item: item.entity_id
        )

        scene_dependencies: list[SceneDependencySummary] = []

        for entry in registry.entities.values():
            if entry.domain != "scene":
                continue

            name = entry.name or entry.original_name or entry.entity_id

            scene_dependency = scene_dependency_from_entities(
                entry.entity_id,
                name,
                entities_in_scene(hass, entry.entity_id),
            )

            scene_dependencies.append(
                SceneDependencySummary(
                    entity_id=scene_dependency.scene_entity_id,
                    name=scene_dependency.name,
                    referenced_entities=list(
                        scene_dependency.referenced_entities
                    ),
                    referenced_entity_count=(
                        scene_dependency.referenced_entity_count
                    ),
                )
            )

        scene_dependencies.sort(
            key=lambda item: item.entity_id
        )

        state = EntitiesState(
            total_entities=len(states),
            domain_counts=dict(sorted(domain_counts.items())),
            unavailable_count=len(unavailable_entities),
            unknown_count=len(unknown_entities),
            unavailable_domains=dict(sorted(unavailable_domains.items())),
            unknown_domains=dict(sorted(unknown_domains.items())),
            unavailable_entities=unavailable_entities,
            unknown_entities=unknown_entities,
            duplicate_name_count=len(duplicate_names),
            duplicate_names=duplicate_names,
            disabled_automation_count=len(disabled_automations),
            disabled_automations=disabled_automations,
            automation_dependency_count=len(automation_dependencies),
            automation_dependencies=automation_dependencies,
            script_dependency_count=len(script_dependencies),
            script_dependencies=script_dependencies,
            scene_dependency_count=len(scene_dependencies),
            scene_dependencies=scene_dependencies,
            unassigned_area_count=len(unassigned_area_entities),
            unassigned_area_entities=unassigned_area_entities,
        )

        context.entities = state
