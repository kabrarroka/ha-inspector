"""Stable public API contract for HA Inspector."""

from __future__ import annotations

from typing import Any

from .capabilities import CAPABILITIES_SCHEMA_VERSION
from .result import RESULT_SCHEMA_VERSION

PUBLIC_API_VERSION = 1

PUBLIC_SERVICES = (
    "run",
    "list_profiles",
    "describe_profile",
    "info",
    "list_acknowledgements",
    "acknowledge_finding",
    "clear_acknowledgement",
    "clear_acknowledgements",
    "export_diagnostic_report",
    "dependency_diagnostics",
    "entity_dependency",
)


def describe_public_api() -> dict[str, Any]:
    """Return the stable public API contract."""
    return {
        "api_version": PUBLIC_API_VERSION,
        "schemas": {
            "capabilities": CAPABILITIES_SCHEMA_VERSION,
            "result": RESULT_SCHEMA_VERSION,
        },
        "services": list(PUBLIC_SERVICES),
    }


__all__ = [
    "PUBLIC_API_VERSION",
    "PUBLIC_SERVICES",
    "describe_public_api",
]
