"""Configuration reference classification helpers for HA Inspector."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConfigurationReferenceClassification:
    """Represent active and disabled references for one configuration type."""

    configuration_type: str
    active_configuration_count: int
    disabled_configuration_count: int
    active_reference_count: int
    disabled_reference_count: int


def _classify_configuration_references(
    configuration_type: str,
    dependencies: Iterable[tuple[str, Iterable[str], bool]],
) -> ConfigurationReferenceClassification:
    """Classify configuration references as active or disabled."""
    active_configurations: set[str] = set()
    disabled_configurations: set[str] = set()

    active_references: set[tuple[str, str]] = set()
    disabled_references: set[tuple[str, str]] = set()

    for configuration_entity_id, entity_ids, disabled in dependencies:
        configurations = (
            disabled_configurations
            if disabled
            else active_configurations
        )
        references = (
            disabled_references
            if disabled
            else active_references
        )

        configurations.add(configuration_entity_id)

        for entity_id in entity_ids:
            references.add((configuration_entity_id, entity_id))

    return ConfigurationReferenceClassification(
        configuration_type=configuration_type,
        active_configuration_count=len(active_configurations),
        disabled_configuration_count=len(disabled_configurations),
        active_reference_count=len(active_references),
        disabled_reference_count=len(disabled_references),
    )


def classify_configuration_references(
    automation_dependencies: Iterable[
        tuple[str, Iterable[str], bool]
    ],
    script_dependencies: Iterable[
        tuple[str, Iterable[str], bool]
    ],
    scene_dependencies: Iterable[
        tuple[str, Iterable[str], bool]
    ],
) -> tuple[ConfigurationReferenceClassification, ...]:
    """Classify references grouped by configuration type."""
    return (
        _classify_configuration_references(
            "automation",
            automation_dependencies,
        ),
        _classify_configuration_references(
            "script",
            script_dependencies,
        ),
        _classify_configuration_references(
            "scene",
            scene_dependencies,
        ),
    )
