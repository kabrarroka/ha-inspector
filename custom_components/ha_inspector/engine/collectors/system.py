"""System information collector for HA Inspector."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
import platform
import sys
from typing import TYPE_CHECKING, Any

from homeassistant.const import __version__ as HA_VERSION
from homeassistant.helpers.system_info import async_get_system_info

from ..context import InspectionContext
from .base import BaseCollector

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


def _installed_version_from_update_entity(
    hass: HomeAssistant,
    entity_id: str,
) -> str | None:
    """Return the installed version exposed by a Home Assistant update entity."""
    state = hass.states.get(entity_id)
    if state is None:
        return None

    installed_version = state.attributes.get("installed_version")
    if isinstance(installed_version, str) and installed_version:
        return installed_version

    return None


def _frontend_version() -> str | None:
    """Return the installed Home Assistant Frontend package version."""
    try:
        return version("home-assistant-frontend")
    except PackageNotFoundError:
        return None


class SystemCollector(BaseCollector):
    """Collect general information about Home Assistant and the host."""

    collector_id = "system"

    async def collect(
        self,
        hass: HomeAssistant,
        context: InspectionContext,
    ) -> None:
        """Collect system and installation information."""
        ha_system_info = await async_get_system_info(hass)

        supervisor_version = _installed_version_from_update_entity(
            hass,
            "update.home_assistant_supervisor",
        )
        operating_system_version = _installed_version_from_update_entity(
            hass,
            "update.home_assistant_operating_system",
        )

        system_info: dict[str, Any] = {
            "home_assistant_version": HA_VERSION,
            "installation_type": ha_system_info.get("installation_type"),
            "supervisor_version": supervisor_version,
            "operating_system_version": operating_system_version,
            "frontend_version": _frontend_version(),
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "architecture": platform.machine(),
            "platform": platform.system(),
            "platform_release": platform.release(),
            "os_name": ha_system_info.get("os_name"),
            "os_version": ha_system_info.get("os_version"),
            "docker": ha_system_info.get("docker"),
            "hassio": ha_system_info.get("hassio"),
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
