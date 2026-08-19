"""Tests for the system collector."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.ha_inspector.engine.collectors import system as system_module
from custom_components.ha_inspector.engine.collectors.system import (
    SystemCollector,
    _CpuMetrics,
    _MemoryMetrics,
)
from custom_components.ha_inspector.engine.context import InspectionContext


class FakeHass:
    def __init__(self) -> None:
        self.data = {}
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

    async def async_add_executor_job(self, func):
        return func()


@pytest.mark.asyncio
async def test_collect_system_information(monkeypatch) -> None:
    monkeypatch.setattr(
        system_module,
        "_collect_time_synchronization",
        lambda hass: True,
    )
    monkeypatch.setattr(
        system_module,
        "_collect_cpu_metrics",
        lambda: _CpuMetrics(
            cpu_percent=12.5,
            cpu_count_logical=4,
            cpu_count_physical=2,
            load_1m=0.75,
            load_5m=0.50,
            load_15m=0.25,
        ),
    )
    monkeypatch.setattr(
        system_module,
        "_collect_memory_metrics",
        lambda: _MemoryMetrics(
            total_bytes=8_000,
            available_bytes=5_000,
            used_bytes=3_000,
            percent=37.5,
        ),
    )
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

    assert state.cpu_percent == 12.5
    assert state.cpu_count_logical == 4
    assert state.cpu_count_physical == 2
    assert state.load_1m == 0.75
    assert state.load_5m == 0.50
    assert state.load_15m == 0.25

    assert state.memory_total_bytes == 8_000
    assert state.memory_available_bytes == 5_000
    assert state.memory_used_bytes == 3_000
    assert state.memory_percent == 37.5


@pytest.mark.asyncio
async def test_collect_system_optional_urls(monkeypatch) -> None:
    monkeypatch.setattr(
        system_module,
        "_collect_time_synchronization",
        lambda hass: True,
    )
    monkeypatch.setattr(
        system_module,
        "_collect_cpu_metrics",
        lambda: _CpuMetrics(
            cpu_percent=0.0,
            cpu_count_logical=None,
            cpu_count_physical=None,
            load_1m=None,
            load_5m=None,
            load_15m=None,
        ),
    )
    monkeypatch.setattr(
        system_module,
        "_collect_memory_metrics",
        lambda: _MemoryMetrics(
            total_bytes=8_000,
            available_bytes=5_000,
            used_bytes=3_000,
            percent=37.5,
        ),
    )
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


def test_collect_cpu_metrics(monkeypatch) -> None:
    class FakePsutil:
        @staticmethod
        def cpu_percent(*, interval):
            assert interval == 0.1
            return 27.5

        @staticmethod
        def cpu_count(*, logical):
            return 4 if logical else 2

    class FakeWrapper:
        def __init__(self):
            self.psutil = FakePsutil()

    monkeypatch.setattr(
        system_module.ha_psutil,
        "PsutilWrapper",
        FakeWrapper,
    )
    monkeypatch.setattr(
        system_module.os,
        "getloadavg",
        lambda: (1.25, 0.75, 0.50),
    )

    metrics = system_module._collect_cpu_metrics()

    assert metrics.cpu_percent == 27.5
    assert metrics.cpu_count_logical == 4
    assert metrics.cpu_count_physical == 2
    assert metrics.load_1m == 1.25
    assert metrics.load_5m == 0.75
    assert metrics.load_15m == 0.50


def test_collect_cpu_metrics_without_loadavg(monkeypatch) -> None:
    class FakePsutil:
        @staticmethod
        def cpu_percent(*, interval):
            assert interval == 0.1
            return 5.0

        @staticmethod
        def cpu_count(*, logical):
            return None

    class FakeWrapper:
        def __init__(self):
            self.psutil = FakePsutil()

    def unavailable_loadavg():
        raise OSError

    monkeypatch.setattr(
        system_module.ha_psutil,
        "PsutilWrapper",
        FakeWrapper,
    )
    monkeypatch.setattr(
        system_module.os,
        "getloadavg",
        unavailable_loadavg,
    )

    metrics = system_module._collect_cpu_metrics()

    assert metrics.cpu_percent == 5.0
    assert metrics.cpu_count_logical is None
    assert metrics.cpu_count_physical is None
    assert metrics.load_1m is None
    assert metrics.load_5m is None
    assert metrics.load_15m is None


def test_collect_memory_metrics(monkeypatch) -> None:
    class FakeMemory:
        total = 16_000
        available = 6_000
        used = 10_000
        percent = 62.5

    class FakePsutil:
        @staticmethod
        def virtual_memory():
            return FakeMemory()

    class FakeWrapper:
        def __init__(self):
            self.psutil = FakePsutil()

    monkeypatch.setattr(
        system_module.ha_psutil,
        "PsutilWrapper",
        FakeWrapper,
    )

    metrics = system_module._collect_memory_metrics()

    assert metrics.total_bytes == 16_000
    assert metrics.available_bytes == 6_000
    assert metrics.used_bytes == 10_000
    assert metrics.percent == 62.5



@pytest.mark.asyncio
async def test_collect_system_restart_history(monkeypatch) -> None:
    monkeypatch.setattr(
        system_module,
        "_collect_time_synchronization",
        lambda hass: True,
    )
    monkeypatch.setattr(
        system_module,
        "_collect_cpu_metrics",
        lambda: _CpuMetrics(
            cpu_percent=10.0,
            cpu_count_logical=4,
            cpu_count_physical=2,
            load_1m=0.1,
            load_5m=0.1,
            load_15m=0.1,
        ),
    )
    monkeypatch.setattr(
        system_module,
        "_collect_memory_metrics",
        lambda: _MemoryMetrics(
            total_bytes=8_000,
            available_bytes=4_000,
            used_bytes=4_000,
            percent=50.0,
        ),
    )

    restart_history = SimpleNamespace(
        restart_counts=lambda: (3, 7)
    )

    hass = FakeHass()
    hass.data = {
        system_module.DOMAIN: {
            system_module.DATA_RESTART_HISTORY: restart_history,
        }
    }

    context = InspectionContext()

    await SystemCollector().collect(hass, context)

    assert context.system.restart_count_24h == 3
    assert context.system.restart_count_7d == 7



@pytest.mark.asyncio
async def test_collect_system_time_synchronization(monkeypatch) -> None:
    monkeypatch.setattr(
        system_module,
        "_collect_cpu_metrics",
        lambda: _CpuMetrics(
            cpu_percent=10.0,
            cpu_count_logical=4,
            cpu_count_physical=2,
            load_1m=0.1,
            load_5m=0.1,
            load_15m=0.1,
        ),
    )
    monkeypatch.setattr(
        system_module,
        "_collect_memory_metrics",
        lambda: _MemoryMetrics(
            total_bytes=8_000,
            available_bytes=4_000,
            used_bytes=4_000,
            percent=50.0,
        ),
    )
    monkeypatch.setattr(
        system_module,
        "_collect_time_synchronization",
        lambda hass: False,
    )

    hass = FakeHass()
    context = InspectionContext()

    await SystemCollector().collect(hass, context)

    assert context.system.time_synchronized is False
