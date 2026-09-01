"""Entity dependency summary helpers for HA Inspector."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EntityDependencySummary:
    """Represent known configuration references to one entity."""

    entity_id: str
    reference_count: int
    automation_references: tuple[str, ...]
    script_references: tuple[str, ...]
    scene_references: tuple[str, ...]


def build_entity_dependency_summaries(
    automation_dependencies: Iterable[tuple[str, Iterable[str]]],
    script_dependencies: Iterable[tuple[str, Iterable[str]]],
    scene_dependencies: Iterable[tuple[str, Iterable[str]]],
) -> tuple[EntityDependencySummary, ...]:
    """Build inverse dependency summaries grouped by referenced entity."""
    automation_references: defaultdict[str, set[str]] = defaultdict(set)
    script_references: defaultdict[str, set[str]] = defaultdict(set)
    scene_references: defaultdict[str, set[str]] = defaultdict(set)

    for source_entity_id, referenced_entities in automation_dependencies:
        for entity_id in referenced_entities:
            automation_references[entity_id].add(source_entity_id)

    for source_entity_id, referenced_entities in script_dependencies:
        for entity_id in referenced_entities:
            script_references[entity_id].add(source_entity_id)

    for source_entity_id, referenced_entities in scene_dependencies:
        for entity_id in referenced_entities:
            scene_references[entity_id].add(source_entity_id)

    entity_ids = (
        set(automation_references)
        | set(script_references)
        | set(scene_references)
    )

    return tuple(
        EntityDependencySummary(
            entity_id=entity_id,
            reference_count=(
                len(automation_references[entity_id])
                + len(script_references[entity_id])
                + len(scene_references[entity_id])
            ),
            automation_references=tuple(
                sorted(automation_references[entity_id])
            ),
            script_references=tuple(
                sorted(script_references[entity_id])
            ),
            scene_references=tuple(
                sorted(scene_references[entity_id])
            ),
        )
        for entity_id in sorted(entity_ids)
    )


def find_entity_dependency(
    summaries: Iterable[EntityDependencySummary],
    entity_id: str,
) -> EntityDependencySummary | None:
    """Return the dependency summary for one entity, if known."""
    return next(
        (
            summary
            for summary in summaries
            if summary.entity_id == entity_id
        ),
        None,
    )
