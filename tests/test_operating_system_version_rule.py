"""Tests for the Home Assistant Operating System version rule."""

import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.rules.operating_system_version import (
    OperatingSystemVersionRule,
)
from custom_components.ha_inspector.engine.severity import Severity


@pytest.mark.asyncio
async def test_stable_os_version_has_no_findings() -> None:
    """Stable HAOS versions must not generate findings."""
    context = InspectionContext(
        system={"operating_system_version": "18.1"}
    )

    findings = await OperatingSystemVersionRule().check(context)

    assert findings == []


@pytest.mark.asyncio
@pytest.mark.parametrize("version", [None, "", "   "])
async def test_missing_os_version_has_no_findings(
    version: str | None,
) -> None:
    """Missing HAOS versions may be valid for other install types."""
    context = InspectionContext(
        system={"operating_system_version": version}
    )

    findings = await OperatingSystemVersionRule().check(context)

    assert findings == []


@pytest.mark.asyncio
async def test_os_beta_version_generates_info() -> None:
    """HAOS beta versions must generate an INFO finding."""
    context = InspectionContext(
        system={"operating_system_version": "18.0.beta2"}
    )

    findings = await OperatingSystemVersionRule().check(context)

    assert len(findings) == 1
    assert findings[0].finding_id == "OPERATING_SYSTEM_VERSION_BETA"
    assert findings[0].severity is Severity.INFO


@pytest.mark.asyncio
async def test_os_release_candidate_generates_info() -> None:
    """HAOS release candidates must generate an INFO finding."""
    context = InspectionContext(
        system={"operating_system_version": "17.3.rc1"}
    )

    findings = await OperatingSystemVersionRule().check(context)

    assert len(findings) == 1
    assert (
        findings[0].finding_id
        == "OPERATING_SYSTEM_VERSION_RELEASE_CANDIDATE"
    )
    assert findings[0].severity is Severity.INFO


@pytest.mark.asyncio
async def test_os_development_version_generates_info() -> None:
    """HAOS development versions must generate an INFO finding."""
    context = InspectionContext(
        system={"operating_system_version": "18.0.dev0"}
    )

    findings = await OperatingSystemVersionRule().check(context)

    assert len(findings) == 1
    assert (
        findings[0].finding_id
        == "OPERATING_SYSTEM_VERSION_DEVELOPMENT"
    )
    assert findings[0].severity is Severity.INFO


@pytest.mark.asyncio
async def test_invalid_os_version_generates_warning() -> None:
    """A present but invalid HAOS version must generate a warning."""
    context = InspectionContext(
        system={"operating_system_version": "not-a-version"}
    )

    findings = await OperatingSystemVersionRule().check(context)

    assert len(findings) == 1
    assert findings[0].finding_id == "OPERATING_SYSTEM_VERSION_UNKNOWN"
    assert findings[0].severity is Severity.WARNING
    assert (
        findings[0].title
        == "Unable to determine Home Assistant OS version"
    )
