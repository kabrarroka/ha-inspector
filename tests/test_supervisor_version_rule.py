"""Tests for the Home Assistant Supervisor version rule."""

import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.rules.supervisor_version import (
    SupervisorVersionRule,
)
from custom_components.ha_inspector.engine.severity import Severity


@pytest.mark.asyncio
async def test_stable_supervisor_version_has_no_findings() -> None:
    """Stable Supervisor versions must not generate findings."""
    context = InspectionContext(
        system={"supervisor_version": "2026.07.3"}
    )

    findings = await SupervisorVersionRule().check(context)

    assert findings == []


@pytest.mark.asyncio
@pytest.mark.parametrize("version", [None, "", "   "])
async def test_missing_supervisor_version_has_no_findings(
    version: str | None,
) -> None:
    """Missing versions are handled by SupervisorAvailabilityRule."""
    context = InspectionContext(system={"supervisor_version": version})

    findings = await SupervisorVersionRule().check(context)

    assert findings == []


@pytest.mark.asyncio
async def test_beta_supervisor_version_generates_info() -> None:
    """Beta Supervisor versions must generate an informational finding."""
    context = InspectionContext(
        system={"supervisor_version": "2026.8.0b2"}
    )

    findings = await SupervisorVersionRule().check(context)

    assert len(findings) == 1
    assert findings[0].finding_id == "SUPERVISOR_VERSION_BETA"
    assert findings[0].severity is Severity.INFO
    assert findings[0].title == "Running a Supervisor beta version"


@pytest.mark.asyncio
async def test_release_candidate_supervisor_version_generates_info() -> None:
    """Supervisor release candidates must generate an INFO finding."""
    context = InspectionContext(
        system={"supervisor_version": "2026.8.0rc1"}
    )

    findings = await SupervisorVersionRule().check(context)

    assert len(findings) == 1
    assert (
        findings[0].finding_id
        == "SUPERVISOR_VERSION_RELEASE_CANDIDATE"
    )
    assert findings[0].severity is Severity.INFO
    assert (
        findings[0].title
        == "Running a Supervisor release candidate"
    )


@pytest.mark.asyncio
async def test_development_supervisor_version_generates_info() -> None:
    """Development Supervisor versions must generate an INFO finding."""
    context = InspectionContext(
        system={"supervisor_version": "2026.8.0.dev0"}
    )

    findings = await SupervisorVersionRule().check(context)

    assert len(findings) == 1
    assert findings[0].finding_id == "SUPERVISOR_VERSION_DEVELOPMENT"
    assert findings[0].severity is Severity.INFO
    assert (
        findings[0].title
        == "Running a Supervisor development version"
    )


@pytest.mark.asyncio
async def test_invalid_supervisor_version_generates_warning() -> None:
    """A present but invalid Supervisor version must generate a warning."""
    context = InspectionContext(
        system={"supervisor_version": "not-a-version"}
    )

    findings = await SupervisorVersionRule().check(context)

    assert len(findings) == 1
    assert findings[0].finding_id == "SUPERVISOR_VERSION_UNKNOWN"
    assert findings[0].severity is Severity.WARNING
    assert (
        findings[0].title
        == "Unable to determine Supervisor version"
    )
