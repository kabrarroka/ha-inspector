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
    from .engine.request import InspectionRequest

SERVICE_RUN = "run"


def _load_engine() -> tuple[
    type[Inspector],
    EngineRegistry,
    type[InspectionRequest],
]:
    """Import and initialize the engine outside Home Assistant's event loop."""
    from .engine.inspector import Inspector
    from .engine.registry import EngineRegistry
    from .engine.request import InspectionRequest

    return Inspector, EngineRegistry.discover(), InspectionRequest


def _service_request_data(
    call: ServiceCall,
) -> dict[str, Any]:
    """Return request data supplied to the inspection service."""
    return {
        "include_rule_ids": call.data.get("include_rule_ids"),
        "include_categories": call.data.get("include_categories"),
        "include_tags": call.data.get("include_tags"),
        "exclude_rule_ids": call.data.get("exclude_rule_ids"),
        "exclude_categories": call.data.get("exclude_categories"),
        "exclude_tags": call.data.get("exclude_tags"),
        "diagnostics": call.data.get("diagnostics", False),
    }


async def async_setup(
    hass: HomeAssistant,
    config: ConfigType,
) -> bool:
    """Set up the HA Inspector integration."""
    inspector_type, registry, request_type = (
        await hass.async_add_executor_job(_load_engine)
    )

    async def async_handle_run(
        call: ServiceCall,
    ) -> ServiceResponse:
        """Run an HA Inspector inspection."""
        inspector = inspector_type(
            collectors=registry.create_collectors(),
            rules=registry.create_rules(),
        )

        request = request_type.from_dict(
            _service_request_data(call),
        )

        result = await inspector.run(
            hass,
            request=request,
        )

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
