"""The HA Inspector integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

if TYPE_CHECKING:
    from .engine.inspector import Inspector
    from .engine.registry import EngineRegistry

SERVICE_RUN = "run"


def _load_engine() -> tuple[type[Inspector], EngineRegistry]:
    """Import and initialize the engine outside Home Assistant's event loop."""
    from .engine.inspector import Inspector
    from .engine.registry import EngineRegistry

    return Inspector, EngineRegistry.discover()


async def async_setup(
    hass: HomeAssistant,
    config: ConfigType,
) -> bool:
    """Set up the HA Inspector integration."""
    inspector_type, registry = await hass.async_add_executor_job(_load_engine)

    async def async_handle_run(
        call: ServiceCall,
    ) -> ServiceResponse:
        """Run an HA Inspector inspection."""
        inspector = inspector_type(
            collectors=registry.create_collectors(),
            rules=registry.create_rules(),
        )

        result = await inspector.run(hass)
        result.metadata["registry"] = {
            "collectors": list(registry.collector_ids),
            "rules": list(registry.rule_ids),
        }
        return result.as_dict()

    hass.services.async_register(
        DOMAIN,
        SERVICE_RUN,
        async_handle_run,
        supports_response=SupportsResponse.ONLY,
    )

    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up HA Inspector from a config entry."""
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload a HA Inspector config entry."""
    return True
