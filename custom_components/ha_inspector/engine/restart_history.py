"""Persistent Home Assistant restart history for HA Inspector."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Final

from homeassistant.helpers.storage import Store

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_STORAGE_VERSION: Final = 1
_STORAGE_KEY: Final = "ha_inspector.restart_history"
_RETENTION_DAYS: Final = 30


class RestartHistory:
    """Store recent Home Assistant start timestamps."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize restart history."""
        self._store = Store[dict[str, list[str]]](
            hass,
            _STORAGE_VERSION,
            _STORAGE_KEY,
        )
        self._starts: list[datetime] = []

    async def async_load(self) -> None:
        """Load persisted start timestamps."""
        data = await self._store.async_load()

        if not data:
            self._starts = []
            return

        starts: list[datetime] = []

        for value in data.get("starts", []):
            try:
                parsed = datetime.fromisoformat(value)
            except (TypeError, ValueError):
                continue

            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)

            starts.append(parsed.astimezone(UTC))

        self._starts = sorted(starts)
        self._prune(datetime.now(UTC))

    async def async_record_start(
        self,
        now: datetime | None = None,
    ) -> None:
        """Record the current Home Assistant start."""
        if now is None:
            now = datetime.now(UTC)

        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        now = now.astimezone(UTC)

        self._starts.append(now)
        self._prune(now)

        await self._store.async_save(
            {
                "starts": [
                    timestamp.isoformat()
                    for timestamp in self._starts
                ]
            }
        )

    def restart_counts(
        self,
        now: datetime | None = None,
    ) -> tuple[int, int]:
        """Return restart counts for the last 24 hours and 7 days."""
        if now is None:
            now = datetime.now(UTC)

        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        now = now.astimezone(UTC)

        cutoff_24h = now - timedelta(hours=24)
        cutoff_7d = now - timedelta(days=7)

        starts_24h = sum(
            timestamp >= cutoff_24h
            for timestamp in self._starts
        )
        starts_7d = sum(
            timestamp >= cutoff_7d
            for timestamp in self._starts
        )

        observed_before_24h = any(
            timestamp < cutoff_24h
            for timestamp in self._starts
        )
        observed_before_7d = any(
            timestamp < cutoff_7d
            for timestamp in self._starts
        )

        # The first ever observed start establishes the baseline. Once the
        # observation history extends beyond a window, every start inside
        # that window represents a restart.
        restart_count_24h = starts_24h
        restart_count_7d = starts_7d

        if not observed_before_24h:
            restart_count_24h = max(restart_count_24h - 1, 0)

        if not observed_before_7d:
            restart_count_7d = max(restart_count_7d - 1, 0)

        return restart_count_24h, restart_count_7d

    def _prune(self, now: datetime) -> None:
        """Remove timestamps outside the retention window."""
        cutoff = now - timedelta(days=_RETENTION_DAYS)
        self._starts = [
            timestamp
            for timestamp in self._starts
            if timestamp >= cutoff
        ]
