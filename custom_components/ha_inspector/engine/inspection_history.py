"""Persistent inspection history for HA Inspector."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any, Final

from homeassistant.helpers.storage import Store

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .historical_comparison import (
        HistoricalDomainComparison,
        HistoricalInspectionComparison,
        HistoricalRemediationComparison,
    )
    from .trends import DomainTrend, HealthChange, ScoreTrend

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

    def domain_trends(self) -> dict[str, DomainTrend]:
        """Return health-score trends for persisted inspection domains."""
        from .trends import domain_health_trends

        return domain_health_trends(self._entries)

    def latest_health_change(self) -> HealthChange:
        """Return the latest global health-score change."""
        from .trends import latest_health_change

        return latest_health_change(self._entries)

    def latest_comparison(
        self,
    ) -> HistoricalInspectionComparison | None:
        """Compare the two most recent persisted inspections."""
        if len(self._entries) < 2:
            return None

        from .historical_comparison import compare_history_entries

        return compare_history_entries(
            self._entries[-2],
            self._entries[-1],
        )

    def latest_domain_comparisons(
        self,
    ) -> dict[str, HistoricalDomainComparison] | None:
        """Compare domains between the two latest persisted inspections."""
        if len(self._entries) < 2:
            return None

        from .historical_comparison import compare_history_domains

        return compare_history_domains(
            self._entries[-2],
            self._entries[-1],
        )

    def latest_remediation_comparison(
        self,
    ) -> HistoricalRemediationComparison | None:
        """Compare remediation lifecycle between latest inspections."""
        if len(self._entries) < 2:
            return None

        from .historical_comparison import compare_remediation_history

        return compare_remediation_history(
            self._entries[-2],
            self._entries[-1],
        )

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

        remediation = InspectionHistory._build_remediation_entry(result)

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
            "remediation": remediation,
        }

    @staticmethod
    def _build_remediation_entry(
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """Build compact remediation history data."""
        progress = result.get("remediation_progress", {})
        if not isinstance(progress, dict):
            progress = {}

        resolved_items = InspectionHistory._history_items(
            result.get("resolved_remediation_items")
        )
        new_reference_items = InspectionHistory._history_items(
            result.get("new_remediation_reference_items")
        )

        return {
            "tracked_entities": InspectionHistory._history_count(
                progress.get("tracked_entities")
            ),
            "pending": InspectionHistory._history_count(
                progress.get("pending")
            ),
            "in_progress": InspectionHistory._history_count(
                progress.get("in_progress")
            ),
            "resolved": InspectionHistory._history_count(
                progress.get("resolved")
            ),
            "total_actions": InspectionHistory._history_count(
                progress.get("total_actions")
            ),
            "completed_actions": InspectionHistory._history_count(
                progress.get("completed_actions")
            ),
            "remaining_actions": InspectionHistory._history_count(
                progress.get("remaining_actions")
            ),
            "new_references": InspectionHistory._history_count(
                progress.get("new_references")
            ),
            "resolved_items": resolved_items,
            "new_reference_items": new_reference_items,
        }

    @staticmethod
    def _history_count(value: object) -> int:
        """Normalize one remediation history counter."""
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        return 0

    @staticmethod
    def _history_items(value: object) -> list[dict[str, Any]]:
        """Normalize compact remediation history items."""
        if not isinstance(value, (list, tuple)):
            return []

        return [
            deepcopy(item)
            for item in value
            if isinstance(item, dict)
        ]
