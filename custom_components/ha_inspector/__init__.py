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
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.typing import ConfigType

from .const import (
    DATA_LAST_RESULT,
    DOMAIN,
    PLATFORMS,
    SIGNAL_INSPECTION_FINISHED,
)

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

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(DATA_LAST_RESULT, None)

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

        result_dict = result.as_dict()
        hass.data[DOMAIN][DATA_LAST_RESULT] = result_dict
        async_dispatcher_send(hass, SIGNAL_INSPECTION_FINISHED, result_dict)

        return result_dict

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
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload a HA Inspector config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
