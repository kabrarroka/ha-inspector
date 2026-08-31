"""Scene dependency inspection helpers for HA Inspector."""

from __future__ import annotations

from dataclasses import dataclass

from .entity_references import EntityReference, valid_entity_ids


@dataclass(frozen=True, slots=True)
class SceneDependency:
    """Represent resolved entity dependencies for one scene."""

    scene_entity_id: str
    name: str
    references: tuple[EntityReference, ...]

    @property
    def referenced_entities(self) -> tuple[str, ...]:
        """Return unique referenced entity IDs in discovery order."""
        return tuple(
            dict.fromkeys(
                reference.entity_id for reference in self.references
            )
        )

    @property
    def referenced_entity_count(self) -> int:
        """Return the number of unique referenced entities."""
        return len(self.referenced_entities)


def scene_dependency_from_entities(
    scene_entity_id: str,
    name: str,
    entity_ids: list[str],
) -> SceneDependency:
    """Build a scene dependency from Home Assistant resolved entities."""
    references = tuple(
        EntityReference(
            entity_id=entity_id,
            path=(),
        )
        for entity_id in valid_entity_ids(entity_ids)
    )

    return SceneDependency(
        scene_entity_id=scene_entity_id,
        name=name,
        references=references,
    )
