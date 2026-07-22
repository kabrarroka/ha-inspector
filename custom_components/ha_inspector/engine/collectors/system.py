"""System information collector for HA Inspector."""

from __future__ import annotations

import platform
import sys
from typing import TYPE_CHECKING, Any

from homeassistant.const import __version__ as HA_VERSION

from ..context import InspectionContext
from .base import BaseCollector

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class SystemCollector(BaseCollector):
    """Collect general information about Home Assistant and the host."""

    collector_id = "system"

    async def collect(
        self,
        hass: HomeAssistant,
        context: InspectionContext,
    ) -> None:
        """Collect system information."""
        system_info: dict[str, Any] = {
            "home_assistant_version": HA_VERSION,
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "architecture": platform.machine(),
            "platform": platform.system(),
            "platform_release": platform.release(),
            "timezone": hass.config.time_zone,
            "latitude": hass.config.latitude,
            "longitude": hass.config.longitude,
            "elevation": hass.config.elevation,
            "currency": hass.config.currency,
            "country": hass.config.country,
            "language": hass.config.language,
            "config_directory": hass.config.config_dir,
            "internal_url": hass.config.internal_url,
            "external_url": hass.config.external_url,
            "python_executable": sys.executable,
        }

        context.system.update(system_info)