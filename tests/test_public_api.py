"""Tests for the stable HA Inspector public API."""

from custom_components.ha_inspector.engine import (
    CAPABILITIES_SCHEMA_VERSION,
    PUBLIC_API_VERSION,
    PUBLIC_SERVICES,
    RESULT_SCHEMA_VERSION,
    EngineCapabilities,
    Finding,
    InspectionProfile,
    InspectionRequest,
    InspectionResult,
    Severity,
    describe_engine,
    describe_public_api,
    get_profile,
    list_profiles,
)


def test_public_api_versions() -> None:
    """Public API exposes stable schema versions."""
    assert PUBLIC_API_VERSION == 1
    assert CAPABILITIES_SCHEMA_VERSION == 1
    assert RESULT_SCHEMA_VERSION == 2


def test_public_api_services_are_stable() -> None:
    """Public service names are explicitly declared."""
    assert PUBLIC_SERVICES == (
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
    )


def test_describe_public_api() -> None:
    """Public API description is JSON-safe and deterministic."""
    assert describe_public_api() == {
        "api_version": 1,
        "schemas": {
            "capabilities": 1,
            "result": 2,
        },
        "services": [
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
        ],
    }


def test_engine_public_exports_are_importable() -> None:
    """Stable engine symbols are available from the package root."""
    assert EngineCapabilities is not None
    assert Finding is not None
    assert InspectionProfile is not None
    assert InspectionRequest is not None
    assert InspectionResult is not None
    assert Severity is not None
    assert describe_engine is not None
    assert get_profile is not None
    assert list_profiles is not None
