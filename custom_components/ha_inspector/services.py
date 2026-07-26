"""Registration of HA Inspector Home Assistant service actions."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import voluptuous as vol

from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .engine.inspection_service import InspectionRequestError
from .service_adapter import (
    InspectionServiceAdapter,
    InspectionServiceAdapterError,
)

SERVICE_RUN_INSPECTION = "run_inspection"

ATTR_PROFILE = "profile"
ATTR_RULE_IDS = "rule_ids"
ATTR_CATEGORIES = "categories"
ATTR_TAGS = "tags"
ATTR_EXCLUDE_RULE_IDS = "exclude_rule_ids"
ATTR_EXCLUDE_CATEGORIES = "exclude_categories"
ATTR_EXCLUDE_TAGS = "exclude_tags"
ATTR_STRICT = "strict"

_STRING_LIST = vol.All(cv.ensure_list, [cv.string])

SERVICE_RUN_INSPECTION_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_PROFILE): cv.string,
        vol.Optional(ATTR_RULE_IDS): _STRING_LIST,
        vol.Optional(ATTR_CATEGORIES): _STRING_LIST,
        vol.Optional(ATTR_TAGS): _STRING_LIST,
        vol.Optional(ATTR_EXCLUDE_RULE_IDS): _STRING_LIST,
        vol.Optional(ATTR_EXCLUDE_CATEGORIES): _STRING_LIST,
        vol.Optional(ATTR_EXCLUDE_TAGS): _STRING_LIST,
        vol.Optional(ATTR_STRICT, default=True): cv.boolean,
    },
    extra=vol.PREVENT_EXTRA,
)

ContextFactory = Callable[[HomeAssistant, ServiceCall], Any]


def _default_context_factory(
    hass: HomeAssistant,
    call: ServiceCall,
) -> HomeAssistant:
    """Return the Home Assistant object as inspection context."""
    return hass


def async_register_services(
    hass: HomeAssistant,
    adapter: InspectionServiceAdapter,
    *,
    context_factory: ContextFactory = _default_context_factory,
) -> None:
    """Register HA Inspector service actions.

    Registration is idempotent so repeated setup paths do not replace an
    already registered handler.
    """
    if hass.services.has_service(DOMAIN, SERVICE_RUN_INSPECTION):
        return

    async def async_handle_run_inspection(
        call: ServiceCall,
    ) -> ServiceResponse:
        """Run an inspection and return its serialized result."""
        context = context_factory(hass, call)

        try:
            return await adapter.async_handle(context, call.data)
        except (
            InspectionRequestError,
            InspectionServiceAdapterError,
            KeyError,
        ) as err:
            raise ServiceValidationError(str(err)) from err
        except HomeAssistantError:
            raise
        except Exception as err:
            raise HomeAssistantError(
                "HA Inspector could not complete the inspection"
            ) from err

    hass.services.async_register(
        DOMAIN,
        SERVICE_RUN_INSPECTION,
        async_handle_run_inspection,
        schema=SERVICE_RUN_INSPECTION_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )


def async_unregister_services(hass: HomeAssistant) -> None:
    """Remove HA Inspector service actions."""
    if hass.services.has_service(DOMAIN, SERVICE_RUN_INSPECTION):
        hass.services.async_remove(
            DOMAIN,
            SERVICE_RUN_INSPECTION,
        )


__all__ = [
    "ATTR_CATEGORIES",
    "ATTR_EXCLUDE_CATEGORIES",
    "ATTR_EXCLUDE_RULE_IDS",
    "ATTR_EXCLUDE_TAGS",
    "ATTR_PROFILE",
    "ATTR_RULE_IDS",
    "ATTR_STRICT",
    "ATTR_TAGS",
    "SERVICE_RUN_INSPECTION",
    "SERVICE_RUN_INSPECTION_SCHEMA",
    "async_register_services",
    "async_unregister_services",
]
