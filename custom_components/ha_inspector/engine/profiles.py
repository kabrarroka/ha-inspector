"""Built-in inspection profiles."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from .i18n import normalize_language
from .request import InspectionRequest


class InspectionProfileError(ValueError):
    """Raised when an inspection profile cannot be resolved."""


@dataclass(frozen=True, slots=True)
class InspectionProfile:
    """Describe a reusable inspection configuration."""

    profile_id: str
    title: str
    description: str
    request: InspectionRequest

    def as_dict(
        self,
        language: str | None = None,
    ) -> dict[str, object]:
        """Return a JSON-safe localized representation."""
        title, description = _localized_profile_text(
            self,
            language,
        )

        return {
            "profile_id": self.profile_id,
            "title": title,
            "description": description,
            "request": self.request.as_dict(),
        }

    def as_summary(
        self,
        language: str | None = None,
    ) -> dict[str, str]:
        """Return the localized summary representation."""
        title, description = _localized_profile_text(
            self,
            language,
        )

        return {
            "profile_id": self.profile_id,
            "title": title,
            "description": description,
        }

_BUILT_IN_PROFILES: dict[str, InspectionProfile] = {
    "full": InspectionProfile(
        profile_id="full",
        title="Full inspection",
        description="Run every registered inspection rule.",
        request=InspectionRequest(),
    ),
    "quick": InspectionProfile(
        profile_id="quick",
        title="Quick inspection",
        description=(
            "Run a reduced set of high-value system and availability checks."
        ),
        request=InspectionRequest(
            include_rule_ids=(
                "CORE_VERSION",
                "SUPERVISOR_AVAILABILITY",
                "SUPERVISOR_VERSION",
                "OPERATING_SYSTEM_VERSION",
                "RECORDER_AVAILABILITY",
                "INTEGRATION_SETUP_ERRORS",
                "UNAVAILABLE_ENTITIES",
            ),
        ),
    ),
    "system": InspectionProfile(
        profile_id="system",
        title="System inspection",
        description="Inspect Home Assistant system and platform information.",
        request=InspectionRequest(
            include_rule_ids=(
                "CORE_VERSION",
                "FRONTEND_VERSION",
                "INSTALLATION_CONSISTENCY",
                "OPERATING_SYSTEM_VERSION",
                "SUPERVISOR_AVAILABILITY",
                "SUPERVISOR_VERSION",
                "SYSTEM_INFORMATION",
            ),
        ),
    ),
    "entities": InspectionProfile(
        profile_id="entities",
        title="Entity inspection",
        description="Inspect entity availability, state and naming.",
        request=InspectionRequest(
            include_rule_ids=(
                "DUPLICATE_ENTITY_NAMES",
                "UNAVAILABLE_ENTITIES",
                "UNKNOWN_ENTITIES",
            ),
        ),
    ),
    "integrations": InspectionProfile(
        profile_id="integrations",
        title="Integration inspection",
        description="Inspect integration setup and lifecycle errors.",
        request=InspectionRequest(
            include_rule_ids=(
                "INTEGRATION_LIFECYCLE_ERRORS",
                "INTEGRATION_SETUP_ERRORS",
                "INTEGRATION_SETUP_RETRIES",
            ),
        ),
    ),
    "recorder": InspectionProfile(
        profile_id="recorder",
        title="Recorder inspection",
        description="Inspect recorder availability and retention settings.",
        request=InspectionRequest(
            include_rule_ids=(
                "RECORDER_AVAILABILITY",
                "RECORDER_KEEP_DAYS",
            ),
        ),
    ),
    "storage": InspectionProfile(
        profile_id="storage",
        title="Storage inspection",
        description="Inspect storage availability and free disk space.",
        request=InspectionRequest(
            include_rule_ids=(
                "DISK_FREE_SPACE",
            ),
        ),
    ),
}



_PROFILE_TRANSLATIONS: Mapping[
    str,
    Mapping[str, tuple[str, str]],
] = MappingProxyType(
    {
        "es": MappingProxyType(
            {
                "full": (
                    "Inspección completa",
                    "Ejecuta todas las reglas de inspección registradas.",
                ),
                "quick": (
                    "Inspección rápida",
                    "Ejecuta un conjunto reducido de comprobaciones "
                    "importantes del sistema y de disponibilidad.",
                ),
                "system": (
                    "Inspección del sistema",
                    "Inspecciona la información del sistema y de la "
                    "plataforma de Home Assistant.",
                ),
                "entities": (
                    "Inspección de entidades",
                    "Inspecciona la disponibilidad, el estado y los "
                    "nombres de las entidades.",
                ),
                "integrations": (
                    "Inspección de integraciones",
                    "Inspecciona errores de configuración y del ciclo "
                    "de vida de las integraciones.",
                ),
                "recorder": (
                    "Inspección del registrador",
                    "Inspecciona la disponibilidad del registrador y "
                    "la configuración de retención.",
                ),
                "storage": (
                    "Inspección del almacenamiento",
                    "Inspecciona la disponibilidad del almacenamiento "
                    "y el espacio libre en disco.",
                ),
            }
        ),
    }
)


def _localized_profile_text(
    profile: InspectionProfile,
    language: str | None,
) -> tuple[str, str]:
    """Return localized profile title and description."""
    selected_language = normalize_language(language)

    translation = _PROFILE_TRANSLATIONS.get(
        selected_language,
        {},
    ).get(profile.profile_id)

    if translation is None:
        return profile.title, profile.description

    return translation


PROFILES: Mapping[str, InspectionProfile] = MappingProxyType(
    _BUILT_IN_PROFILES
)


def normalize_profile_id(profile_id: str) -> str:
    """Normalize a profile identifier."""
    if not isinstance(profile_id, str):
        raise InspectionProfileError(
            "Inspection profile identifier must be a string"
        )

    normalized = profile_id.strip().lower()

    if not normalized:
        raise InspectionProfileError(
            "Inspection profile identifier cannot be empty"
        )

    return normalized


def get_profile(profile_id: str) -> InspectionProfile:
    """Return a built-in inspection profile."""
    normalized = normalize_profile_id(profile_id)

    try:
        return PROFILES[normalized]
    except KeyError as err:
        available = ", ".join(sorted(PROFILES))
        raise InspectionProfileError(
            f"Unknown inspection profile {profile_id!r}. "
            f"Available profiles: {available}"
        ) from err


def create_profile_request(
    profile_id: str,
    *,
    diagnostics: bool | None = None,
) -> InspectionRequest:
    """Create an independent request from a built-in profile."""
    profile = get_profile(profile_id)
    request_data = profile.request.as_dict()

    if diagnostics is not None:
        request_data["diagnostics"] = diagnostics

    return InspectionRequest.from_dict(request_data)


def list_profiles() -> tuple[InspectionProfile, ...]:
    """Return built-in profiles in deterministic order."""
    return tuple(
        PROFILES[profile_id]
        for profile_id in sorted(PROFILES)
    )


__all__ = [
    "PROFILES",
    "InspectionProfile",
    "InspectionProfileError",
    "create_profile_request",
    "get_profile",
    "list_profiles",
    "normalize_profile_id",
]
