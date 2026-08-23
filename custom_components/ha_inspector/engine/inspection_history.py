"""Persistent inspection history for HA Inspector."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any, Final

from homeassistant.helpers.storage import Store

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .trends import ScoreTrend

_STORAGE_VERSION: Final = 1
_STORAGE_KEY: Final = "ha_inspector.inspection_history"
_MAX_ENTRIES: Final = 100


class InspectionHistory:
    """Store compact summaries of recent HA Inspector executions."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize inspection history."""
        self._store = Store[dict[str, list[dict[str, Any]]]](
            hass,
            _STORAGE_VERSION,
            _STORAGE_KEY,
        )
        self._entries: list[dict[str, Any]] = []

    async def async_load(self) -> None:
        """Load persisted inspection summaries."""
        data = await self._store.async_load()

        if not data:
            self._entries = []
            return

        entries = data.get("entries", [])

        if not isinstance(entries, list):
            self._entries = []
            return

        self._entries = [
            deepcopy(entry)
            for entry in entries[-_MAX_ENTRIES:]
            if isinstance(entry, dict)
        ]

    async def async_add(
        self,
        result: dict[str, Any],
    ) -> None:
        """Add a compact inspection summary."""
        entry = self._build_entry(result)

        self._entries.append(entry)
        self._entries = self._entries[-_MAX_ENTRIES:]

        await self._store.async_save(
            {
                "entries": deepcopy(self._entries),
            }
        )

    def entries(self) -> list[dict[str, Any]]:
        """Return persisted inspection summaries."""
        return deepcopy(self._entries)

    def score_trend(self) -> ScoreTrend:
        """Return the health-score trend for persisted inspections."""
        from .trends import health_score_trend

        return health_score_trend(self._entries)

    @staticmethod
    def _build_entry(
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """Build a compact history entry from an inspection result."""
        metadata = result.get("metadata", {})
        profile = (
            metadata.get("profile")
            if isinstance(metadata, dict)
            else None
        )

        dashboard_summary = result.get("dashboard_summary", {})
        if not isinstance(dashboard_summary, dict):
            dashboard_summary = {}

        domain_health = result.get("domain_health", {})
        if not isinstance(domain_health, dict):
            domain_health = {}

        return {
            "started_at": result.get("started_at"),
            "finished_at": result.get("finished_at"),
            "duration_seconds": result.get("duration_seconds"),
            "score": result.get("score"),
            "status": dashboard_summary.get("status"),
            "total_findings": result.get("total_findings"),
            "summary": deepcopy(result.get("summary", {})),
            "domain_health": deepcopy(domain_health),
            "profile": profile,
        }
