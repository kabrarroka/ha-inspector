"""Stable public interface for the HA Inspector engine."""

from .capabilities import (
    CAPABILITIES_SCHEMA_VERSION,
    EngineCapabilities,
    describe_engine,
)
from .models import Finding
from .profiles import (
    InspectionProfile,
    InspectionProfileError,
    create_profile_request,
    get_profile,
    list_profiles,
)
from .public_api import (
    PUBLIC_API_VERSION,
    PUBLIC_SERVICES,
    describe_public_api,
)
from .request import InspectionRequest
from .result import RESULT_SCHEMA_VERSION, InspectionResult
from .severity import Severity

__all__ = [
    "CAPABILITIES_SCHEMA_VERSION",
    "PUBLIC_API_VERSION",
    "PUBLIC_SERVICES",
    "RESULT_SCHEMA_VERSION",
    "EngineCapabilities",
    "Finding",
    "InspectionProfile",
    "InspectionProfileError",
    "InspectionRequest",
    "InspectionResult",
    "Severity",
    "create_profile_request",
    "describe_engine",
    "describe_public_api",
    "get_profile",
    "list_profiles",
]
