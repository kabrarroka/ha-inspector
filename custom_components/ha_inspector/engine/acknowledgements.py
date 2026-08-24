"""Persistent finding acknowledgements for HA Inspector."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

_STORAGE_VERSION = 1
_STORAGE_KEY = "ha_inspector.acknowledgements"


class AcknowledgementStore:
    """Persist acknowledged finding identifiers."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the acknowledgement store."""
        self._store: Store[dict[str, Any]] = Store(
            hass,
            _STORAGE_VERSION,
            _STORAGE_KEY,
        )
        self._finding_ids: set[str] = set()

    @property
    def finding_ids(self) -> frozenset[str]:
        """Return acknowledged finding identifiers."""
        return frozenset(self._finding_ids)

    async def async_load(self) -> None:
        """Load persisted acknowledgements."""
        data = await self._store.async_load()

        if not isinstance(data, dict):
            return

        finding_ids = data.get("finding_ids")

        if not isinstance(finding_ids, list):
            return

        self._finding_ids = {
            value.strip()
            for value in finding_ids
            if isinstance(value, str) and value.strip()
        }

    async def async_acknowledge(self, finding_id: str) -> None:
        """Acknowledge and persist a finding identifier."""
        normalized = finding_id.strip()

        if not normalized:
            raise ValueError("Finding identifier cannot be empty")

        self._finding_ids.add(normalized)
        await self._async_save()

    async def async_clear(self, finding_id: str) -> None:
        """Clear and persist one acknowledged finding identifier."""
        normalized = finding_id.strip()

        if not normalized:
            raise ValueError("Finding identifier cannot be empty")

        self._finding_ids.discard(normalized)
        await self._async_save()

    async def async_clear_all(self) -> None:
        """Clear all acknowledged finding identifiers."""
        self._finding_ids.clear()
        await self._async_save()

    async def _async_save(self) -> None:
        """Persist current acknowledgement state."""
        await self._store.async_save(
            {
                "finding_ids": sorted(self._finding_ids),
            }
        )


__all__ = ["AcknowledgementStore"]
