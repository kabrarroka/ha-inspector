"""System information collector for HA Inspector."""

from __future__ import annotations

import importlib.util
import os
import platform
import sys
from contextlib import suppress
from dataclasses import dataclass
from typing import TYPE_CHECKING

import psutil_home_assistant as ha_psutil  # type: ignore[import-untyped]
from homeassistant.const import __version__ as HA_VERSION

from ..context import InspectionContext
from ..system_state import SystemState
from .base import BaseCollector

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


@dataclass(frozen=True, slots=True)
class _CpuMetrics:
    """Represent collected host CPU metrics."""

    cpu_percent: float
    cpu_count_logical: int | None
    cpu_count_physical: int | None
    load_1m: float | None
    load_5m: float | None
    load_15m: float | None


@dataclass(frozen=True, slots=True)
class _MemoryMetrics:
    """Represent collected host memory metrics."""

    total_bytes: int
    available_bytes: int
    used_bytes: int
    percent: float


def _collect_cpu_metrics() -> _CpuMetrics:
    """Collect host CPU metrics."""
    load_1m: float | None = None
    load_5m: float | None = None
    load_15m: float | None = None

    with suppress(OSError):
        load_1m, load_5m, load_15m = os.getloadavg()

    # PsutilWrapper currently expects importlib.util to be loaded.
    _ = importlib.util
    psutil = ha_psutil.PsutilWrapper().psutil

    return _CpuMetrics(
        cpu_percent=float(psutil.cpu_percent(interval=0.1)),
        cpu_count_logical=psutil.cpu_count(logical=True),
        cpu_count_physical=psutil.cpu_count(logical=False),
        load_1m=load_1m,
        load_5m=load_5m,
        load_15m=load_15m,
    )


def _collect_memory_metrics() -> _MemoryMetrics:
    """Collect host memory metrics."""
    # PsutilWrapper currently expects importlib.util to be loaded.
    _ = importlib.util
    psutil = ha_psutil.PsutilWrapper().psutil
    memory = psutil.virtual_memory()

    return _MemoryMetrics(
        total_bytes=int(memory.total),
        available_bytes=int(memory.available),
        used_bytes=int(memory.used),
        percent=float(memory.percent),
    )


class SystemCollector(BaseCollector):
    """Collect general information about Home Assistant and the host."""

    collector_id = "system"

    async def collect(
        self,
        hass: HomeAssistant,
        context: InspectionContext,
    ) -> None:
        """Collect system information."""
        cpu_metrics = await hass.async_add_executor_job(_collect_cpu_metrics)
        memory_metrics = await hass.async_add_executor_job(
            _collect_memory_metrics
        )

        state = SystemState(
            home_assistant_version=HA_VERSION,
            python_version=platform.python_version(),
            python_implementation=platform.python_implementation(),
            architecture=platform.machine(),
            platform=platform.system(),
            platform_release=platform.release(),
            timezone=hass.config.time_zone,
            latitude=hass.config.latitude,
            longitude=hass.config.longitude,
            elevation=hass.config.elevation,
            currency=hass.config.currency,
            country=hass.config.country,
            language=hass.config.language,
            config_directory=hass.config.config_dir,
            internal_url=hass.config.internal_url,
            external_url=hass.config.external_url,
            python_executable=sys.executable,
            cpu_percent=cpu_metrics.cpu_percent,
            cpu_count_logical=cpu_metrics.cpu_count_logical,
            cpu_count_physical=cpu_metrics.cpu_count_physical,
            load_1m=cpu_metrics.load_1m,
            load_5m=cpu_metrics.load_5m,
            load_15m=cpu_metrics.load_15m,
            memory_total_bytes=memory_metrics.total_bytes,
            memory_available_bytes=memory_metrics.available_bytes,
            memory_used_bytes=memory_metrics.used_bytes,
            memory_percent=memory_metrics.percent,
        )

        context.system = state
