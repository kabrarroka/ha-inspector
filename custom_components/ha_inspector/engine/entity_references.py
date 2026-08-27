"""Entity reference discovery helpers for HA Inspector."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

type ReferencePathPart = str | int
type ReferencePath = tuple[ReferencePathPart, ...]

_ENTITY_ID_PATTERN = re.compile(
    r"(?<![a-z0-9_-])"
    r"(?P<entity_id>[a-z0-9_]+\.[a-z0-9_]+)"
    r"(?![a-z0-9_-])"
)


@dataclass(frozen=True, slots=True)
class EntityReference:
    """Represent one discovered entity-reference candidate."""

    entity_id: str
    path: ReferencePath


def discover_entity_references(value: object) -> list[EntityReference]:
    """Discover entity-reference candidates in a nested configuration value."""
    references: list[EntityReference] = []
    seen: set[EntityReference] = set()

    def visit(current: object, path: ReferencePath) -> None:
        if isinstance(current, str):
            for match in _ENTITY_ID_PATTERN.finditer(current):
                reference = EntityReference(
                    entity_id=match.group("entity_id"),
                    path=path,
                )
                if reference not in seen:
                    seen.add(reference)
                    references.append(reference)
            return

        if isinstance(current, Mapping):
            for key, nested_value in current.items():
                visit(nested_value, (*path, str(key)))
            return

        if isinstance(current, Sequence) and not isinstance(
            current,
            (str, bytes, bytearray),
        ):
            for index, nested_value in enumerate(current):
                visit(nested_value, (*path, index))

    visit(value, ())
    return references
