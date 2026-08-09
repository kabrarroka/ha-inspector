"""Entity state and registry collector for HA Inspector."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import TYPE_CHECKING

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.helpers import entity_registry as er

from ..context import InspectionContext
from .base import BaseCollector
from ..entities_state import (
    DisabledAutomation,
    DuplicateEntityName,
    EntitiesState,
    EntitySummary,
)

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
        )

        context.entities = state
