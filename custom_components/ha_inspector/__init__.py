"""The HA Inspector integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .engine.collectors import (
    EntitiesCollector,
    IntegrationsCollector,
    RecorderCollector,
    SystemCollector,
)
from .engine.inspector import Inspector
from .engine.rules import (
    IntegrationLifecycleErrorRule,
    IntegrationSetupErrorRule,
    IntegrationSetupRetryRule,
    RecorderAvailabilityRule,
    RecorderKeepDaysRule,
    SystemInformationRule,
    UnavailableEntitiesRule,
    UnknownEntitiesRule,
)

SERVICE_RUN = "run"


async def async_setup(
    hass: HomeAssistant,
    config: ConfigType,
) -> bool:
    """Set up the HA Inspector integration."""

    async def async_handle_run(
        call: ServiceCall,
    ) -> ServiceResponse:
        """Run an HA Inspector inspection."""
        inspector = Inspector(
            collectors=[
                SystemCollector(),
                RecorderCollector(),
                IntegrationsCollector(),
                EntitiesCollector(),
            ],
            rules=[
                SystemInformationRule(),
                RecorderAvailabilityRule(),
                RecorderKeepDaysRule(),
                IntegrationSetupErrorRule(),
                IntegrationSetupRetryRule(),
                IntegrationLifecycleErrorRule(),
                UnavailableEntitiesRule(),
                UnknownEntitiesRule(),
            ],
)

        result = await inspector.run(hass)
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