"""Config flow for the HA Inspector integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_PERIODIC_INSPECTION_ENABLED,
    CONF_PERIODIC_INSPECTION_INTERVAL,
    CONF_PERIODIC_INSPECTION_PROFILE,
    DEFAULT_PERIODIC_INSPECTION_ENABLED,
    DEFAULT_PERIODIC_INSPECTION_INTERVAL,
    DEFAULT_PERIODIC_INSPECTION_PROFILE,
    DOMAIN,
    MAX_PERIODIC_INSPECTION_INTERVAL,
    MIN_PERIODIC_INSPECTION_INTERVAL,
    NAME,
)
from .engine.profiles import list_profiles


class HAInspectorConfigFlow(  # type: ignore[call-arg]
    config_entries.ConfigFlow,  # type: ignore[misc]
    domain=DOMAIN,
):
    """Handle a config flow for HA Inspector."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> HAInspectorOptionsFlow:
        """Return the options flow."""
        return HAInspectorOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title=NAME, data={})

        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))


class HAInspectorOptionsFlow(
    config_entries.OptionsFlow,  # type: ignore[misc]
):
    """Manage HA Inspector options."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Configure periodic inspections."""
        options = self.config_entry.options

        profiles = {
            profile.profile_id: profile.profile_id
            for profile in list_profiles()
        }

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_PERIODIC_INSPECTION_ENABLED,
                    default=options.get(
                        CONF_PERIODIC_INSPECTION_ENABLED,
                        DEFAULT_PERIODIC_INSPECTION_ENABLED,
                    ),
                ): bool,
                vol.Required(
                    CONF_PERIODIC_INSPECTION_INTERVAL,
                    default=options.get(
                        CONF_PERIODIC_INSPECTION_INTERVAL,
                        DEFAULT_PERIODIC_INSPECTION_INTERVAL,
                    ),
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(
                        min=MIN_PERIODIC_INSPECTION_INTERVAL,
                        max=MAX_PERIODIC_INSPECTION_INTERVAL,
                    ),
                ),
                vol.Required(
                    CONF_PERIODIC_INSPECTION_PROFILE,
                    default=options.get(
                        CONF_PERIODIC_INSPECTION_PROFILE,
                        DEFAULT_PERIODIC_INSPECTION_PROFILE,
                    ),
                ): vol.In(profiles),
            }
        )

        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                validated = schema(user_input)
            except vol.Invalid:
                errors["base"] = "invalid_options"
            else:
                return self.async_create_entry(
                    title="",
                    data=validated,
                )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
