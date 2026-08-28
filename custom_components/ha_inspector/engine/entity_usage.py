"""Known entity usage inspection helpers for HA Inspector."""

from __future__ import annotations

from collections.abc import Iterable

EXCLUDED_UNREFERENCED_DOMAINS = frozenset(
    {
        "automation",
        "scene",
        "script",
    }
)


def referenced_entity_ids(
    dependency_entities: Iterable[Iterable[str]],
) -> set[str]:
    """Return the unique entity IDs referenced by known dependencies."""
    return {
        entity_id
        for entities in dependency_entities
        for entity_id in entities
    }


def unreferenced_entity_ids(
    entity_ids: Iterable[str],
    referenced_entities: Iterable[str],
    *,
    excluded_domains: frozenset[str] = EXCLUDED_UNREFERENCED_DOMAINS,
) -> tuple[str, ...]:
    """Return entities not referenced by known dependency sources."""
    referenced = set(referenced_entities)

    return tuple(
        sorted(
            entity_id
            for entity_id in set(entity_ids)
            if entity_id not in referenced
            and entity_id.split(".", 1)[0] not in excluded_domains
        )
    )
