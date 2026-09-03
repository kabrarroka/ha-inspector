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
SERVICE_EXPORT_DIAGNOSTIC_REPORT = "export_diagnostic_report"
SERVICE_DEPENDENCY_DIAGNOSTICS = "dependency_diagnostics"
SERVICE_ENTITY_DEPENDENCY = "entity_dependency"
SERVICE_REMEDIATION_PLAN = "remediation_plan"

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
SERVICE_EXPORT_DIAGNOSTIC_REPORT_SCHEMA = vol.Schema({})
SERVICE_DEPENDENCY_DIAGNOSTICS_SCHEMA = vol.Schema({})
SERVICE_ENTITY_DEPENDENCY_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): str,
    }
)

SERVICE_REMEDIATION_PLAN_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): str,
    }
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

    async def async_handle_dependency_diagnostics(
        call: ServiceCall,
    ) -> ServiceResponse:
        """Return dependency diagnostics from the latest inspection."""
        del call

        result = hass.data.setdefault(DOMAIN, {}).get(DATA_LAST_RESULT)

        if not isinstance(result, Mapping):
            from .engine.dependency_diagnostics import (
                empty_dependency_diagnostics,
            )

            return dict(empty_dependency_diagnostics())

        dashboard_summary = result.get("dashboard_summary", {})

        if not isinstance(dashboard_summary, Mapping):
            from .engine.dependency_diagnostics import (
                empty_dependency_diagnostics,
            )

            return dict(empty_dependency_diagnostics())

        dependencies = dashboard_summary.get("dependencies", {})

        if not isinstance(dependencies, Mapping):
            from .engine.dependency_diagnostics import (
                empty_dependency_diagnostics,
            )

            return dict(empty_dependency_diagnostics())

        return {
            "affected_entities": dependencies.get("affected_entities", 0),
            "unavailable": dependencies.get("unavailable", 0),
            "unknown": dependencies.get("unknown", 0),
            "critical": dependencies.get("critical", 0),
            "high": dependencies.get("high", 0),
            "medium": dependencies.get("medium", 0),
            "low": dependencies.get("low", 0),
            "max_impact_score": dependencies.get("max_impact_score", 0),
        }

    hass.services.async_register(
        DOMAIN,
        SERVICE_DEPENDENCY_DIAGNOSTICS,
        async_handle_dependency_diagnostics,
        schema=SERVICE_DEPENDENCY_DIAGNOSTICS_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    async def async_handle_entity_dependency(
        call: ServiceCall,
    ) -> ServiceResponse:
        """Return dependency information for one entity."""
        from homeassistant.helpers import entity_registry as er

        from .engine.cleanup_recommendations import (
            build_cleanup_recommendation,
        )
        from .engine.entity_dependency_impact_summary import (
            build_entity_dependency_impact_summary,
        )
        from .engine.live_dependency_context import (
            build_live_stale_reference_context,
        )

        entity_id = str(call.data["entity_id"])
        registry = er.async_get(hass)
        context = build_live_stale_reference_context(hass, entity_id)
        impact = build_entity_dependency_impact_summary(context)

        exists = any(
            entry.entity_id == entity_id
            for entry in registry.entities.values()
        ) or hass.states.get(entity_id) is not None

        cleanup_recommendation = None

        if not exists:
            recommendation = build_cleanup_recommendation(context)

            if recommendation is not None:
                cleanup_recommendation = {
                    "action": recommendation.action,
                    "safety": recommendation.safety,
                    "reason": recommendation.reason,
                    "affected_configurations": list(
                        recommendation.affected_configurations
                    ),
                }

        return {
            "entity_id": entity_id,
            "exists": exists,
            "referenced": impact.reference_count > 0,
            "reference_count": impact.reference_count,
            "active_reference_count": impact.active_reference_count,
            "disabled_reference_count": impact.disabled_reference_count,
            "automation_reference_count": (
                impact.automation_reference_count
            ),
            "script_reference_count": impact.script_reference_count,
            "scene_reference_count": impact.scene_reference_count,
            "active_automation_references": list(
                context.active_automation_references
            ),
            "disabled_automation_references": list(
                context.disabled_automation_references
            ),
            "active_script_references": list(
                context.active_script_references
            ),
            "disabled_script_references": list(
                context.disabled_script_references
            ),
            "active_scene_references": list(
                context.active_scene_references
            ),
            "disabled_scene_references": list(
                context.disabled_scene_references
            ),
            "cleanup_recommendation": cleanup_recommendation,
        }

    hass.services.async_register(
        DOMAIN,
        SERVICE_ENTITY_DEPENDENCY,
        async_handle_entity_dependency,
        schema=SERVICE_ENTITY_DEPENDENCY_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    async def async_handle_remediation_plan(
        call: ServiceCall,
    ) -> ServiceResponse:
        """Return the remediation plan for one entity."""
        from .engine.live_dependency_context import (
            build_live_stale_reference_context,
        )
        from .engine.remediation_plans import (
            build_remediation_plan,
            classify_remediation_plan,
            preview_remediation_impact,
        )

        entity_id = str(call.data["entity_id"])
        context = build_live_stale_reference_context(hass, entity_id)
        plan = build_remediation_plan(context)

        if plan is None:
            return {
                "entity_id": entity_id,
                "plan": None,
                "classification": None,
                "impact_preview": None,
            }

        classification = classify_remediation_plan(plan)
        preview = preview_remediation_impact(plan)

        return {
            "entity_id": entity_id,
            "plan": {
                "action": plan.action,
                "safety": plan.safety,
                "reason": plan.reason,
                "reference_count": plan.reference_count,
                "active_reference_count": plan.active_reference_count,
                "disabled_reference_count": plan.disabled_reference_count,
                "steps": [
                    {
                        "configuration_type": step.configuration_type,
                        "configuration_id": step.configuration_id,
                        "status": step.status,
                        "action": step.action,
                    }
                    for step in plan.steps
                ],
            },
            "classification": {
                "safety": classification.safety,
                "confidence": classification.confidence,
                "reason": classification.reason,
            },
            "impact_preview": {
                "current_reference_count": preview.current_reference_count,
                "affected_configuration_count": (
                    preview.affected_configuration_count
                ),
                "removable_reference_count": (
                    preview.removable_reference_count
                ),
                "review_reference_count": preview.review_reference_count,
                "projected_reference_count": (
                    preview.projected_reference_count
                ),
            },
        }

    hass.services.async_register(
        DOMAIN,
        SERVICE_REMEDIATION_PLAN,
        async_handle_remediation_plan,
        schema=SERVICE_REMEDIATION_PLAN_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    async def async_handle_export_diagnostic_report(
        call: ServiceCall,
    ) -> ServiceResponse:
        """Return an exportable diagnostic report."""
        del call

        result = hass.data.setdefault(DOMAIN, {}).get(DATA_LAST_RESULT)
        if result is None:
            raise RuntimeError(
                "No HA Inspector inspection result is available"
            )

        from .engine.diagnostic_report import build_diagnostic_report

        return build_diagnostic_report(
            version=VERSION,
            result=result,
        )

    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_DIAGNOSTIC_REPORT,
        async_handle_export_diagnostic_report,
        schema=SERVICE_EXPORT_DIAGNOSTIC_REPORT_SCHEMA,
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
