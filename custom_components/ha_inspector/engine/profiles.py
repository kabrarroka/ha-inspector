"""Built-in inspection profiles."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

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

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-safe representation."""
        return {
            "profile_id": self.profile_id,
            "title": self.title,
            "description": self.description,
            "request": self.request.as_dict(),
        }
    def as_summary(self) -> dict[str, str]:
        """Return the summary representation of the profile."""

        return {
            "profile_id": self.profile_id,
            "title": self.title,
            "description": self.description,
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
    "InspectionProfile",
    "InspectionProfileError",
    "PROFILES",
    "create_profile_request",
    "get_profile",
    "list_profiles",
    "normalize_profile_id",
]
