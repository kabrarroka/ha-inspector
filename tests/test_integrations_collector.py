"""Tests for the integrations collector."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.ha_inspector.engine.collectors.integrations import (
    IntegrationsCollector,
)
from custom_components.ha_inspector.engine.context import InspectionContext


class FakeConfigEntries:
    def __init__(self, entries: list[SimpleNamespace]) -> None:
        self._entries = entries

    def async_entries(self) -> list[SimpleNamespace]:
        return self._entries


class FakeHass:
    def __init__(self, entries: list[SimpleNamespace]) -> None:
        self.config_entries = FakeConfigEntries(entries)


def _entry(
    domain: str,
    title: str,
    state: str,
    reason: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        domain=domain,
        title=title,
        state=SimpleNamespace(value=state),
        reason=reason,
    )


@pytest.mark.asyncio
async def test_collect_empty_integrations() -> None:
    context = InspectionContext()

    await IntegrationsCollector().collect(
        FakeHass([]),
        context,
    )

    assert context.integrations.as_dict() == {
        "total_entries": 0,
        "states": {},
        "domains": {},
        "problematic_entries": [],
        "problematic_count": 0,
    }


@pytest.mark.asyncio
async def test_collect_counts_states_and_domains() -> None:
    entries = [
        _entry("mqtt", "MQTT", "loaded"),
        _entry("mqtt", "MQTT 2", "loaded"),
        _entry("hue", "Hue", "not_loaded"),
        _entry("zha", "ZHA", "setup_retry"),
    ]

    context = InspectionContext()

    await IntegrationsCollector().collect(
        FakeHass(entries),
        context,
    )

    integrations = context.integrations

    assert integrations.total_entries == 4

    assert integrations.states == {
        "loaded": 2,
        "not_loaded": 1,
        "setup_retry": 1,
    }

    assert integrations.domains == {
        "hue": 1,
        "mqtt": 2,
        "zha": 1,
    }


@pytest.mark.asyncio
async def test_collect_problematic_integrations() -> None:
    entries = [
        _entry(
            "mqtt",
            "MQTT",
            "setup_error",
            "Connection refused",
        ),
        _entry(
            "zha",
            "ZHA",
            "setup_retry",
            "Retrying",
        ),
        _entry(
            "hue",
            "Hue",
            "migration_error",
            "Migration failed",
        ),
        _entry(
            "esphome",
            "ESPHome",
            "failed_unload",
            "Unload failed",
        ),
        _entry(
            "sun",
            "Sun",
            "loaded",
        ),
    ]

    context = InspectionContext()

    await IntegrationsCollector().collect(
        FakeHass(entries),
        context,
    )

    integrations = context.integrations

    assert integrations.problematic_count == 4

    assert [
        entry.domain
        for entry in integrations.problematic_entries
    ] == [
        "mqtt",
        "zha",
        "hue",
        "esphome",
    ]

    assert integrations.problematic_entries[0].title == "MQTT"
    assert integrations.problematic_entries[0].state == "setup_error"
    assert integrations.problematic_entries[0].reason == "Connection refused"

    assert integrations.problematic_entries[1].state == "setup_retry"
    assert integrations.problematic_entries[2].state == "migration_error"
    assert integrations.problematic_entries[3].state == "failed_unload"


@pytest.mark.asyncio
async def test_collect_ignores_non_problematic_states() -> None:
    entries = [
        _entry("mqtt", "MQTT", "loaded"),
        _entry("hue", "Hue", "not_loaded"),
        _entry("sun", "Sun", "disabled_by"),
    ]

    context = InspectionContext()

    await IntegrationsCollector().collect(
        FakeHass(entries),
        context,
    )

    assert context.integrations.problematic_count == 0
    assert context.integrations.problematic_entries == []