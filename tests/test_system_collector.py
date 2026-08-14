"""Tests for the system collector."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.ha_inspector.engine.collectors import system as system_module
from custom_components.ha_inspector.engine.collectors.system import SystemCollector
from custom_components.ha_inspector.engine.context import InspectionContext


class FakeHass:
    def __init__(self) -> None:
        self.config = SimpleNamespace(
            time_zone="Europe/Madrid",
            latitude=41.65,
            longitude=-4.72,
            elevation=690,
            currency="EUR",
            country="ES",
            language="es",
            config_dir="/config",
            internal_url="http://homeassistant.local:8123",
            external_url="https://example.ui.nabu.casa",
        )


@pytest.mark.asyncio
async def test_collect_system_information(monkeypatch) -> None:
    monkeypatch.setattr(
        system_module,
        "HA_VERSION",
        "2026.8.0",
    )
    monkeypatch.setattr(
        system_module.platform,
        "python_version",
        lambda: "3.14.7",
    )
    monkeypatch.setattr(
        system_module.platform,
        "python_implementation",
        lambda: "CPython",
    )
    monkeypatch.setattr(
        system_module.platform,
        "machine",
        lambda: "x86_64",
    )
    monkeypatch.setattr(
        system_module.platform,
        "system",
        lambda: "Linux",
    )
    monkeypatch.setattr(
        system_module.platform,
        "release",
        lambda: "6.12.0",
    )
    monkeypatch.setattr(
        system_module.sys,
        "executable",
        "/usr/bin/python3",
    )

    context = InspectionContext()

    await SystemCollector().collect(
        FakeHass(),
        context,
    )

    state = context.system

    assert state.home_assistant_version == "2026.8.0"
    assert state.python_version == "3.14.7"
    assert state.python_implementation == "CPython"
    assert state.architecture == "x86_64"
    assert state.platform == "Linux"
    assert state.platform_release == "6.12.0"

    assert state.timezone == "Europe/Madrid"
    assert state.latitude == 41.65
    assert state.longitude == -4.72
    assert state.elevation == 690
    assert state.currency == "EUR"
    assert state.country == "ES"
    assert state.language == "es"

    assert state.config_directory == "/config"
    assert state.internal_url == "http://homeassistant.local:8123"
    assert state.external_url == "https://example.ui.nabu.casa"
    assert state.python_executable == "/usr/bin/python3"


@pytest.mark.asyncio
async def test_collect_system_optional_urls() -> None:
    hass = FakeHass()
    hass.config.internal_url = None
    hass.config.external_url = None

    context = InspectionContext()

    await SystemCollector().collect(
        hass,
        context,
    )

    assert context.system.internal_url is None
    assert context.system.external_url is None