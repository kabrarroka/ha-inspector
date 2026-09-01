"""Stale reference investigation context helpers for HA Inspector."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StaleReferenceContext:
    """Represent investigation context for one stale entity reference."""

    entity_id: str
    active_automation_references: tuple[str, ...]
    disabled_automation_references: tuple[str, ...]
    active_script_references: tuple[str, ...]
    disabled_script_references: tuple[str, ...]
    active_scene_references: tuple[str, ...]
    disabled_scene_references: tuple[str, ...]


def _references_by_status(
    entity_id: str,
    dependencies: Iterable[tuple[str, Iterable[str], bool]],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return active and disabled configurations referencing one entity."""
    active: set[str] = set()
    disabled: set[str] = set()

    for configuration_entity_id, entity_ids, is_disabled in dependencies:
        if entity_id not in entity_ids:
            continue

        references = disabled if is_disabled else active
        references.add(configuration_entity_id)

    return tuple(sorted(active)), tuple(sorted(disabled))


def build_stale_reference_contexts(
    missing_entity_ids: Iterable[str],
    automation_dependencies: Iterable[
        tuple[str, Iterable[str], bool]
    ],
    script_dependencies: Iterable[
        tuple[str, Iterable[str], bool]
    ],
    scene_dependencies: Iterable[
        tuple[str, Iterable[str], bool]
    ],
) -> tuple[StaleReferenceContext, ...]:
    """Build investigation context for missing entity references."""
    missing_entities = tuple(sorted(set(missing_entity_ids)))

    automation_dependencies = tuple(automation_dependencies)
    script_dependencies = tuple(script_dependencies)
    scene_dependencies = tuple(scene_dependencies)

    contexts: list[StaleReferenceContext] = []

    for entity_id in missing_entities:
        active_automations, disabled_automations = _references_by_status(
            entity_id,
            automation_dependencies,
        )
        active_scripts, disabled_scripts = _references_by_status(
            entity_id,
            script_dependencies,
        )
        active_scenes, disabled_scenes = _references_by_status(
            entity_id,
            scene_dependencies,
        )

        contexts.append(
            StaleReferenceContext(
                entity_id=entity_id,
                active_automation_references=active_automations,
                disabled_automation_references=disabled_automations,
                active_script_references=active_scripts,
                disabled_script_references=disabled_scripts,
                active_scene_references=active_scenes,
                disabled_scene_references=disabled_scenes,
            )
        )

    return tuple(contexts)
