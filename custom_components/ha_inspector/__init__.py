"""The HA Inspector integration."""

from __future__ import annotations

from collections.abc import Mapping
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
    VERSION,
)
from .engine.profiles import (
    InspectionProfileError,
    create_profile_request,
)
from .engine.request import InspectionRequest

if TYPE_CHECKING:
    from .engine.inspector import Inspector
    from .engine.registry import EngineRegistry

SERVICE_RUN = "run"

SERVICE_DESCRIBE_PROFILE = "describe_profile"

SERVICE_INFO = "info"

API_VERSION = 1

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

        result = await inspector.run(
            hass,
            request=request,
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

        hass.data.setdefault(DOMAIN, {})[DATA_LAST_RESULT] = result_data
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
        supports_response=SupportsResponse.ONLY,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_DESCRIBE_PROFILE,
        async_handle_describe_profile,
        supports_response=SupportsResponse.ONLY,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_INFO,
        async_handle_info,
        supports_response=SupportsResponse.ONLY,
    )

    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up HA Inspector from a config entry."""
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
