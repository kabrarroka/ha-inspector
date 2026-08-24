"""The HA Inspector integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

import voluptuous as vol
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
    DATA_ACKNOWLEDGEMENTS,
    DATA_INSPECTION_HISTORY,
    DATA_LAST_RESULT,
    DATA_RESTART_HISTORY,
    DOMAIN,
    PLATFORMS,
    SIGNAL_INSPECTION_FINISHED,
    VERSION,
)
from .engine.profiles import (
    InspectionProfileError,
    create_profile_request,
)
from .engine.public_api import (
    PUBLIC_API_VERSION,
    describe_public_api,
)
from .engine.request import InspectionRequest

if TYPE_CHECKING:
    from .engine.inspector import Inspector
    from .engine.registry import EngineRegistry

SERVICE_RUN = "run"

SERVICE_DESCRIBE_PROFILE = "describe_profile"

SERVICE_INFO = "info"

SERVICE_LIST_ACKNOWLEDGEMENTS = "list_acknowledgements"
SERVICE_ACKNOWLEDGE_FINDING = "acknowledge_finding"
SERVICE_CLEAR_ACKNOWLEDGEMENT = "clear_acknowledgement"
SERVICE_CLEAR_ACKNOWLEDGEMENTS = "clear_acknowledgements"

API_VERSION = PUBLIC_API_VERSION

_REQUEST_FIELDS = (
    "include_rule_ids",
    "include_categories",
    "include_tags",
    "exclude_rule_ids",
    "exclude_categories",
    "exclude_tags",
    "diagnostics",
    "language",
)

SERVICE_RUN_SCHEMA = vol.Schema(
    {
        vol.Optional("profile"): vol.Any(str, dict),
        vol.Optional("include_rule_ids"): vol.Any(str, [str]),
        vol.Optional("include_categories"): vol.Any(str, [str]),
        vol.Optional("include_tags"): vol.Any(str, [str]),
        vol.Optional("exclude_rule_ids"): vol.Any(str, [str]),
        vol.Optional("exclude_categories"): vol.Any(str, [str]),
        vol.Optional("exclude_tags"): vol.Any(str, [str]),
        vol.Optional("diagnostics"): bool,
        vol.Optional("language"): str,
    }
)

SERVICE_LIST_PROFILES_SCHEMA = vol.Schema({})

SERVICE_DESCRIBE_PROFILE_SCHEMA = vol.Schema(
    {
        vol.Required("profile_id"): str,
    }
)

SERVICE_INFO_SCHEMA = vol.Schema({})

SERVICE_LIST_ACKNOWLEDGEMENTS_SCHEMA = vol.Schema({})

SERVICE_ACKNOWLEDGE_FINDING_SCHEMA = vol.Schema(
    {
        vol.Required("finding_id"): str,
    }
)

SERVICE_CLEAR_ACKNOWLEDGEMENT_SCHEMA = vol.Schema(
    {
        vol.Required("finding_id"): str,
    }
)

SERVICE_CLEAR_ACKNOWLEDGEMENTS_SCHEMA = vol.Schema({})


def _load_engine() -> tuple[
    type[Inspector],
    EngineRegistry,
]:
    """Import and initialize the engine outside Home Assistant's event loop."""
    from .engine.inspector import Inspector
    from .engine.registry import EngineRegistry

    return Inspector, EngineRegistry.discover()


def _profile_definition(
    value: object,
) -> tuple[str, dict[str, Any]]:
    """Normalize a profile service value."""
    if isinstance(value, str):
        profile_id = value.strip()

        if not profile_id:
            raise InspectionProfileError(
                "Inspection profile identifier cannot be empty"
            )

        return profile_id, {}

    if not isinstance(value, Mapping):
        raise InspectionProfileError(
            "Inspection profile must be a string or mapping"
        )

    mapping_profile_id = value.get("id")

    if (
        not isinstance(mapping_profile_id, str)
        or not mapping_profile_id.strip()
    ):
        raise InspectionProfileError(
            "Inspection profile mapping must contain a non-empty 'id'"
        )

    overrides = value.get("overrides", {})

    if overrides is None:
        overrides = {}

    if not isinstance(overrides, Mapping):
        raise InspectionProfileError(
            "Inspection profile overrides must be a mapping"
        )

    unknown_profile_keys = set(value) - {
        "id",
        "overrides",
    }

    if unknown_profile_keys:
        unknown = ", ".join(sorted(unknown_profile_keys))
        raise InspectionProfileError(
            f"Unknown inspection profile options: {unknown}"
        )

    unknown_override_keys = set(overrides) - set(_REQUEST_FIELDS)

    if unknown_override_keys:
        unknown = ", ".join(sorted(unknown_override_keys))
        raise InspectionProfileError(
            f"Unknown inspection profile overrides: {unknown}"
        )

    return mapping_profile_id.strip(), dict(overrides)


def _explicit_request_data(
    data: Mapping[str, Any],
) -> dict[str, Any]:
    """Return explicitly supplied request fields."""
    return {
        field: data[field]
        for field in _REQUEST_FIELDS
        if field in data
    }


def _build_request(
    data: Mapping[str, Any],
) -> InspectionRequest:
    """Build an inspection request from service data."""
    explicit_data = _explicit_request_data(data)

    if "profile" not in data:
        return InspectionRequest.from_dict(explicit_data)

    profile_id, profile_overrides = _profile_definition(
        data["profile"]
    )

    profile_request = create_profile_request(profile_id)
    request_data = profile_request.as_dict()

    # Priority:
    # profile defaults -> profile overrides -> explicit service fields
    request_data.update(profile_overrides)
    request_data.update(explicit_data)

    return InspectionRequest.from_dict(request_data)


async def async_setup(
    hass: HomeAssistant,
    config: ConfigType,
) -> bool:
    """Set up the HA Inspector integration."""
    inspector_type, registry = await hass.async_add_executor_job(
        _load_engine
    )

    async def async_handle_info(
        call: ServiceCall,
    ) -> ServiceResponse:
        """Return information about the HA Inspector engine."""
        from .engine.profiles import list_profiles

        return {
            "version": VERSION,
            "api_version": API_VERSION,
            "public_api": describe_public_api(),
            "engine": {
                "profiles": len(list_profiles()),
                "rules": len(registry.rule_ids),
                "collectors": len(registry.collector_ids),
            },
    }

    async def async_handle_run(
        call: ServiceCall,
    ) -> ServiceResponse:
        """Run an HA Inspector inspection."""
        inspector = inspector_type(
            collectors=registry.create_collectors(),
            rules=registry.create_rules(),
        )

        request = _build_request(call.data)

        domain_data = hass.data.setdefault(DOMAIN, {})
        acknowledgements = domain_data.get(DATA_ACKNOWLEDGEMENTS)

        suppression = None
        if acknowledgements is not None:
            from .engine.suppression import FindingSuppressionPolicy

            suppression = FindingSuppressionPolicy(
                finding_ids=acknowledgements.finding_ids
            )

        result = await inspector.run(
            hass,
            request=request,
            suppression=suppression,
        )

        result.metadata["registry"] = {
            "collectors": list(registry.collector_ids),
            "rules": list(registry.rule_ids),
        }

        if "profile" in call.data:
            profile_id, _ = _profile_definition(
                call.data["profile"]
            )
            result.metadata["profile"] = profile_id.strip().lower()

        result_data = result.as_dict()

        domain_data[DATA_LAST_RESULT] = result_data

        inspection_history = domain_data.get(DATA_INSPECTION_HISTORY)
        if inspection_history is not None:
            await inspection_history.async_add(result_data)
        async_dispatcher_send(
            hass,
            SIGNAL_INSPECTION_FINISHED,
            result_data,
        )

        return result_data

    hass.services.async_register(
        DOMAIN,
        SERVICE_RUN,
        async_handle_run,
        schema=SERVICE_RUN_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    async def async_handle_list_profiles(
        call: ServiceCall,
    ) -> ServiceResponse:
        """Return the available inspection profiles."""
        from .engine.profiles import list_profiles

        language = getattr(
            getattr(hass, "config", None),
            "language",
            None,
        )

        return {
            "profiles": [
                profile.as_summary(language)
                for profile in list_profiles()
            ]
        }

    async def async_handle_describe_profile(
        call: ServiceCall,
    ) -> ServiceResponse:
        """Return the definition of an inspection profile."""
        from .engine.profiles import get_profile

        profile = get_profile(call.data["profile_id"])

        language = getattr(
            getattr(hass, "config", None),
            "language",
            None,
        )

        return {
            "profile": profile.as_dict(language),
        }

    hass.services.async_register(
        DOMAIN,
        "list_profiles",
        async_handle_list_profiles,
        schema=SERVICE_LIST_PROFILES_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_DESCRIBE_PROFILE,
        async_handle_describe_profile,
        schema=SERVICE_DESCRIBE_PROFILE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_INFO,
        async_handle_info,
        schema=SERVICE_INFO_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    def acknowledgement_store() -> Any:
        """Return the initialized acknowledgement store."""
        store = hass.data.setdefault(DOMAIN, {}).get(
            DATA_ACKNOWLEDGEMENTS
        )
        if store is None:
            raise RuntimeError(
                "HA Inspector acknowledgement store is not initialized"
            )
        return store

    def acknowledgement_response() -> ServiceResponse:
        """Return the current acknowledgement state."""
        finding_ids = sorted(acknowledgement_store().finding_ids)
        return {
            "finding_ids": finding_ids,
            "count": len(finding_ids),
        }

    async def async_handle_list_acknowledgements(
        call: ServiceCall,
    ) -> ServiceResponse:
        """Return acknowledged finding identifiers."""
        return acknowledgement_response()

    async def async_handle_acknowledge_finding(
        call: ServiceCall,
    ) -> ServiceResponse:
        """Persist one acknowledged finding identifier."""
        store = acknowledgement_store()
        await store.async_acknowledge(call.data["finding_id"])
        return acknowledgement_response()

    async def async_handle_clear_acknowledgement(
        call: ServiceCall,
    ) -> ServiceResponse:
        """Clear one acknowledged finding identifier."""
        store = acknowledgement_store()
        await store.async_clear(call.data["finding_id"])
        return acknowledgement_response()

    async def async_handle_clear_acknowledgements(
        call: ServiceCall,
    ) -> ServiceResponse:
        """Clear every acknowledged finding identifier."""
        store = acknowledgement_store()
        await store.async_clear_all()
        return acknowledgement_response()

    hass.services.async_register(
        DOMAIN,
        SERVICE_LIST_ACKNOWLEDGEMENTS,
        async_handle_list_acknowledgements,
        schema=SERVICE_LIST_ACKNOWLEDGEMENTS_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_ACKNOWLEDGE_FINDING,
        async_handle_acknowledge_finding,
        schema=SERVICE_ACKNOWLEDGE_FINDING_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEAR_ACKNOWLEDGEMENT,
        async_handle_clear_acknowledgement,
        schema=SERVICE_CLEAR_ACKNOWLEDGEMENT_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEAR_ACKNOWLEDGEMENTS,
        async_handle_clear_acknowledgements,
        schema=SERVICE_CLEAR_ACKNOWLEDGEMENTS_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up HA Inspector from a config entry."""
    domain_data = hass.data.setdefault(DOMAIN, {})

    if DATA_RESTART_HISTORY not in domain_data:
        from .engine.restart_history import RestartHistory

        restart_history = RestartHistory(hass)
        await restart_history.async_load()
        await restart_history.async_record_start()

        domain_data[DATA_RESTART_HISTORY] = restart_history

    if DATA_INSPECTION_HISTORY not in domain_data:
        from .engine.inspection_history import InspectionHistory

        inspection_history = InspectionHistory(hass)
        await inspection_history.async_load()

        domain_data[DATA_INSPECTION_HISTORY] = inspection_history

    if DATA_ACKNOWLEDGEMENTS not in domain_data:
        from .engine.acknowledgements import AcknowledgementStore

        acknowledgements = AcknowledgementStore(hass)
        await acknowledgements.async_load()

        domain_data[DATA_ACKNOWLEDGEMENTS] = acknowledgements

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload a HA Inspector config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )
    return bool(unloaded)
