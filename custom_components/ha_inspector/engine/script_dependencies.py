"""Script dependency inspection helpers for HA Inspector."""

from __future__ import annotations

from dataclasses import dataclass

from .entity_references import EntityReference


@dataclass(frozen=True, slots=True)
class ScriptDependency:
    """Represent resolved entity dependencies for one script."""

    script_entity_id: str
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


def script_dependency_from_entities(
    script_entity_id: str,
    name: str,
    entity_ids: list[str],
) -> ScriptDependency:
    """Build a script dependency from Home Assistant resolved entities."""
    references = tuple(
        EntityReference(
            entity_id=entity_id,
            path=(),
        )
        for entity_id in sorted(set(entity_ids))
    )

    return ScriptDependency(
        script_entity_id=script_entity_id,
        name=name,
        references=references,
    )
