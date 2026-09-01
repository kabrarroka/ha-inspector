"""Configuration dependency summary helpers for HA Inspector."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConfigurationDependencySummary:
    """Represent dependency statistics for one configuration type."""

    configuration_type: str
    configuration_count: int
    referenced_entity_count: int
    reference_count: int


def _build_configuration_dependency_summary(
    configuration_type: str,
    dependencies: Iterable[tuple[str, Iterable[str]]],
) -> ConfigurationDependencySummary:
    """Build dependency statistics for one configuration type."""
    configurations: set[str] = set()
    referenced_entities: set[str] = set()
    references: set[tuple[str, str]] = set()

    for configuration_entity_id, entity_ids in dependencies:
        configurations.add(configuration_entity_id)

        for entity_id in entity_ids:
            referenced_entities.add(entity_id)
            references.add((configuration_entity_id, entity_id))

    return ConfigurationDependencySummary(
        configuration_type=configuration_type,
        configuration_count=len(configurations),
        referenced_entity_count=len(referenced_entities),
        reference_count=len(references),
    )


def build_configuration_dependency_summaries(
    automation_dependencies: Iterable[tuple[str, Iterable[str]]],
    script_dependencies: Iterable[tuple[str, Iterable[str]]],
    scene_dependencies: Iterable[tuple[str, Iterable[str]]],
) -> tuple[ConfigurationDependencySummary, ...]:
    """Build dependency summaries grouped by configuration type."""
    return (
        _build_configuration_dependency_summary(
            "automation",
            automation_dependencies,
        ),
        _build_configuration_dependency_summary(
            "script",
            script_dependencies,
        ),
        _build_configuration_dependency_summary(
            "scene",
            scene_dependencies,
        ),
    )
