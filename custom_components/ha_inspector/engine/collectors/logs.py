"""System log collector for HA Inspector."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Protocol, cast

from ..context import InspectionContext
from ..logs_state import LogsState
from .base import BaseCollector

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


_SYSTEM_LOG_DOMAIN = "system_log"
_WINDOW = timedelta(hours=24)
_TOP_LOGGERS = 5


class _SystemLogRecords(Protocol):
    """Describe the system log record store used by Home Assistant."""

    def to_list(self) -> list[dict[str, object]]:
        """Return system log records."""


class _SystemLogHandler(Protocol):
    """Describe the Home Assistant system log handler."""

    records: _SystemLogRecords


def _collect_logs_state(
    hass: HomeAssistant,
    *,
    now: datetime | None = None,
) -> LogsState:
    """Collect recent Home Assistant warning and error log statistics."""
    handler_object = hass.data.get(_SYSTEM_LOG_DOMAIN)

    if handler_object is None or not hasattr(handler_object, "records"):
        return LogsState()

    handler = cast(_SystemLogHandler, handler_object)

    try:
        entries = handler.records.to_list()
    except (AttributeError, TypeError):
        return LogsState()

    if now is None:
        now = datetime.now(UTC)

    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)

    cutoff = (now.astimezone(UTC) - _WINDOW).timestamp()

    warning_entries = 0
    error_entries = 0
    critical_entries = 0

    warning_occurrences = 0
    error_occurrences = 0
    critical_occurrences = 0

    logger_occurrences: Counter[str] = Counter()

    for entry in entries:
        timestamp = entry.get("timestamp")

        if not isinstance(timestamp, int | float):
            continue

        if float(timestamp) < cutoff:
            continue

        level = entry.get("level")

        if not isinstance(level, str):
            continue

        raw_count = entry.get("count")
        count = (
            raw_count
            if isinstance(raw_count, int) and raw_count > 0
            else 1
        )

        logger_name = entry.get("name")

        if isinstance(logger_name, str) and logger_name:
            logger_occurrences[logger_name] += count

        normalized_level = level.upper()

        if normalized_level == "WARNING":
            warning_entries += 1
            warning_occurrences += count
        elif normalized_level == "ERROR":
            error_entries += 1
            error_occurrences += count
        elif normalized_level == "CRITICAL":
            critical_entries += 1
            critical_occurrences += count

    top_loggers = [
        {
            "logger": logger_name,
            "occurrences": occurrences,
        }
        for logger_name, occurrences in logger_occurrences.most_common(
            _TOP_LOGGERS
        )
    ]

    return LogsState(
        available=True,
        warning_entries=warning_entries,
        error_entries=error_entries,
        critical_entries=critical_entries,
        warning_occurrences=warning_occurrences,
        error_occurrences=error_occurrences,
        critical_occurrences=critical_occurrences,
        top_loggers=top_loggers,
    )


class LogsCollector(BaseCollector):
    """Collect recent Home Assistant system log statistics."""

    collector_id = "logs"

    async def collect(
        self,
        hass: HomeAssistant,
        context: InspectionContext,
    ) -> None:
        """Collect system log information."""
        context.logs = _collect_logs_state(hass)
