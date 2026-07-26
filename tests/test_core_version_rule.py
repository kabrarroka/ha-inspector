"""Tests for the Home Assistant Core version rule."""

import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.rules.core_version import CoreVersionRule
from custom_components.ha_inspector.engine.severity import Severity


@pytest.mark.asyncio
async def test_stable_core_version_has_no_findings() -> None:
    """Stable Core versions must not generate findings."""
    context = InspectionContext(
        system={"home_assistant_version": "2026.7.2"}
    )

    findings = await CoreVersionRule().check(context)

    assert findings == []


@pytest.mark.asyncio
async def test_beta_core_version_generates_info() -> None:
    """Beta Core versions must generate an informational finding."""
    context = InspectionContext(
        system={"home_assistant_version": "2026.8.0b3"}
    )

    findings = await CoreVersionRule().check(context)

    assert len(findings) == 1
    assert findings[0].finding_id == "CORE_VERSION_BETA"
    assert findings[0].severity is Severity.INFO
    assert findings[0].title == "Running a beta version"


@pytest.mark.asyncio
async def test_release_candidate_generates_info() -> None:
    """Release candidates must generate an informational finding."""
    context = InspectionContext(
        system={"home_assistant_version": "2026.8.0rc2"}
    )

    findings = await CoreVersionRule().check(context)

    assert len(findings) == 1
    assert findings[0].finding_id == "CORE_VERSION_RELEASE_CANDIDATE"
    assert findings[0].severity is Severity.INFO
    assert findings[0].title == "Running a release candidate"


@pytest.mark.asyncio
async def test_development_version_generates_info() -> None:
    """Development Core versions must generate an informational finding."""
    context = InspectionContext(
        system={"home_assistant_version": "2026.8.0.dev0"}
    )

    findings = await CoreVersionRule().check(context)

    assert len(findings) == 1
    assert findings[0].finding_id == "CORE_VERSION_DEVELOPMENT"
    assert findings[0].severity is Severity.INFO
    assert findings[0].title == "Running a development version"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "version",
    [None, "", "not-a-version"],
)
async def test_unknown_core_version_generates_warning(
    version: str | None,
) -> None:
    """Missing and invalid Core versions must generate a warning."""
    context = InspectionContext(
        system={"home_assistant_version": version}
    )

    findings = await CoreVersionRule().check(context)

    assert len(findings) == 1
    assert findings[0].finding_id == "CORE_VERSION_UNKNOWN"
    assert findings[0].severity is Severity.WARNING
    assert findings[0].title == "Unable to determine Core version"
