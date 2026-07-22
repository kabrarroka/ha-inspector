"""Entity state collector for HA Inspector."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Any

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN

from ..context import InspectionContext
from .base import BaseCollector

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class EntitiesCollector(BaseCollector):
    """Collect aggregate information about entity states."""

    collector_id = "entities"

    async def collect(
        self,
        hass: HomeAssistant,
        context: InspectionContext,
    ) -> None:
        """Collect entity state statistics."""
        states = hass.states.async_all()

        domain_counts: Counter[str] = Counter()
        unavailable_domains: Counter[str] = Counter()
        unknown_domains: Counter[str] = Counter()

        unavailable_entities: list[dict[str, Any]] = []
        unknown_entities: list[dict[str, Any]] = []

        for state in states:
            domain = state.domain
            domain_counts[domain] += 1

            entity_summary = {
                "entity_id": state.entity_id,
                "name": state.name,
                "domain": domain,
            }

            if state.state == STATE_UNAVAILABLE:
                unavailable_domains[domain] += 1
                unavailable_entities.append(entity_summary)

            elif state.state == STATE_UNKNOWN:
                unknown_domains[domain] += 1
                unknown_entities.append(entity_summary)

        context.entities.update(
            {
                "total_entities": len(states),
                "domain_counts": dict(sorted(domain_counts.items())),
                "unavailable_count": len(unavailable_entities),
                "unknown_count": len(unknown_entities),
                "unavailable_domains": dict(
                    sorted(unavailable_domains.items())
                ),
                "unknown_domains": dict(
                    sorted(unknown_domains.items())
                ),
                "unavailable_entities": unavailable_entities,
                "unknown_entities": unknown_entities,
            }
        )