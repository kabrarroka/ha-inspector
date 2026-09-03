"""Live dependency reference context helpers for HA Inspector."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .automation_dependencies import automation_dependency_from_entities
from .scene_dependencies import scene_dependency_from_entities
from .script_dependencies import script_dependency_from_entities
from .stale_reference_context import (
    StaleReferenceContext,
    build_stale_reference_contexts,
)


def build_live_stale_reference_context(
    hass: HomeAssistant,
    entity_id: str,
) -> StaleReferenceContext:
    """Build live dependency reference context for one entity."""
    from homeassistant.components.automation import entities_in_automation
    from homeassistant.components.homeassistant.scene import entities_in_scene
    from homeassistant.components.script import entities_in_script

    registry = er.async_get(hass)

    automation_dependencies = []
    script_dependencies = []
    scene_dependencies = []

    for entry in registry.entities.values():
        disabled = entry.disabled_by is not None

        if entry.domain == "automation":
            automation_dependency = automation_dependency_from_entities(
                entry.entity_id,
                entry.name or entry.original_name or entry.entity_id,
                entities_in_automation(hass, entry.entity_id),
            )
            automation_dependencies.append(
                (
                    entry.entity_id,
                    automation_dependency.referenced_entities,
                    disabled,
                )
            )

        elif entry.domain == "script":
            script_dependency = script_dependency_from_entities(
                entry.entity_id,
                entry.name or entry.original_name or entry.entity_id,
                entities_in_script(hass, entry.entity_id),
            )
            script_dependencies.append(
                (
                    entry.entity_id,
                    script_dependency.referenced_entities,
                    disabled,
                )
            )

        elif entry.domain == "scene":
            scene_dependency = scene_dependency_from_entities(
                entry.entity_id,
                entry.name or entry.original_name or entry.entity_id,
                entities_in_scene(hass, entry.entity_id),
            )
            scene_dependencies.append(
                (
                    entry.entity_id,
                    scene_dependency.referenced_entities,
                    disabled,
                )
            )

    return build_stale_reference_contexts(
        (entity_id,),
        automation_dependencies,
        script_dependencies,
        scene_dependencies,
    )[0]
