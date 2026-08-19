"""Tests for the system log collector."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from custom_components.ha_inspector.engine.collectors.logs import (
    LogsCollector,
    _collect_logs_state,
)
from custom_components.ha_inspector.engine.context import InspectionContext

_NOW = datetime(2026, 8, 19, 8, 0, tzinfo=UTC)


class FakeRecords:
    def __init__(self, entries: list[dict[str, object]]) -> None:
        self._entries = entries

    def to_list(self) -> list[dict[str, object]]:
        return self._entries


class FakeHass:
    def __init__(self, entries: list[dict[str, object]] | None = None) -> None:
        self.data: dict[str, object] = {}

        if entries is not None:
            self.data["system_log"] = SimpleNamespace(
                records=FakeRecords(entries)
            )


def test_logs_unavailable_without_system_log() -> None:
    state = _collect_logs_state(FakeHass(), now=_NOW)

    assert state.available is False


def test_logs_collect_recent_entries_and_occurrences() -> None:
    recent = (_NOW - timedelta(hours=1)).timestamp()
    old = (_NOW - timedelta(days=2)).timestamp()

    hass = FakeHass(
        [
            {
                "timestamp": recent,
                "level": "WARNING",
                "name": "homeassistant.components.demo",
                "count": 4,
            },
            {
                "timestamp": recent,
                "level": "ERROR",
                "name": "custom_components.demo",
                "count": 2,
            },
            {
                "timestamp": recent,
                "level": "CRITICAL",
                "name": "custom_components.demo",
                "count": 1,
            },
            {
                "timestamp": old,
                "level": "ERROR",
                "name": "old.logger",
                "count": 99,
            },
        ]
    )

    state = _collect_logs_state(hass, now=_NOW)

    assert state.available is True
    assert state.warning_entries == 1
    assert state.error_entries == 1
    assert state.critical_entries == 1
    assert state.warning_occurrences == 4
    assert state.error_occurrences == 2
    assert state.critical_occurrences == 1

    assert state.top_loggers == [
        {
            "logger": "homeassistant.components.demo",
            "occurrences": 4,
        },
        {
            "logger": "custom_components.demo",
            "occurrences": 3,
        },
    ]


@pytest.mark.asyncio
async def test_logs_collector_sets_context() -> None:
    recent = datetime.now(UTC).timestamp()

    hass = FakeHass(
        [
            {
                "timestamp": recent,
                "level": "ERROR",
                "name": "test.logger",
                "count": 1,
            }
        ]
    )

    context = InspectionContext()

    await LogsCollector().collect(hass, context)

    assert context.logs.available is True
    assert context.logs.error_entries == 1
