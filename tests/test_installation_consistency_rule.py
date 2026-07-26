"""Tests for installation consistency checks."""

import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.rules.installation_consistency import (
    InstallationConsistencyRule,
)
from custom_components.ha_inspector.engine.severity import Severity


async def _check(system: dict) -> list:
    context = InspectionContext(system=system)
    return await InstallationConsistencyRule().check(context)


@pytest.mark.asyncio
async def test_haos_complete_has_no_findings() -> None:
    findings = await _check(
        {
            "installation_type": "Home Assistant OS",
            "supervisor_version": "2026.07.3",
            "operating_system_version": "18.1",
        }
    )
    assert findings == []


@pytest.mark.asyncio
async def test_haos_without_os_version_generates_warning() -> None:
    findings = await _check(
        {
            "installation_type": "Home Assistant OS",
            "supervisor_version": "2026.07.3",
            "operating_system_version": None,
        }
    )
    assert len(findings) == 1
    assert findings[0].finding_id == "HAOS_VERSION_MISSING"
    assert findings[0].severity is Severity.WARNING


@pytest.mark.asyncio
async def test_haos_missing_supervisor_is_not_duplicated() -> None:
    findings = await _check(
        {
            "installation_type": "Home Assistant OS",
            "supervisor_version": None,
            "operating_system_version": "18.1",
        }
    )
    assert findings == []


@pytest.mark.asyncio
async def test_supervised_with_supervisor_has_no_findings() -> None:
    findings = await _check(
        {
            "installation_type": "Home Assistant Supervised",
            "supervisor_version": "2026.07.3",
            "operating_system_version": None,
        }
    )
    assert findings == []


@pytest.mark.asyncio
async def test_supervised_with_haos_version_generates_info() -> None:
    findings = await _check(
        {
            "installation_type": "Supervised",
            "supervisor_version": "2026.07.3",
            "operating_system_version": "18.1",
        }
    )
    assert len(findings) == 1
    assert findings[0].finding_id == "UNEXPECTED_HAOS_VERSION"
    assert findings[0].severity is Severity.INFO


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "installation_type",
    ["Home Assistant Container", "Container", "Home Assistant Core", "Core"],
)
async def test_standalone_installations_without_managed_components_are_valid(
    installation_type: str,
) -> None:
    findings = await _check(
        {
            "installation_type": installation_type,
            "supervisor_version": None,
            "operating_system_version": None,
        }
    )
    assert findings == []


@pytest.mark.asyncio
async def test_container_with_supervisor_generates_warning() -> None:
    findings = await _check(
        {
            "installation_type": "Container",
            "supervisor_version": "2026.07.3",
            "operating_system_version": None,
        }
    )
    assert len(findings) == 1
    assert findings[0].finding_id == "UNEXPECTED_SUPERVISOR"


@pytest.mark.asyncio
async def test_core_with_both_managed_components_generates_two_findings() -> None:
    findings = await _check(
        {
            "installation_type": "Core",
            "supervisor_version": "2026.07.3",
            "operating_system_version": "18.1",
        }
    )
    assert {finding.finding_id for finding in findings} == {
        "UNEXPECTED_SUPERVISOR",
        "UNEXPECTED_HAOS_VERSION",
    }


@pytest.mark.asyncio
async def test_missing_installation_type_generates_warning() -> None:
    findings = await _check({"installation_type": None})
    assert len(findings) == 1
    assert findings[0].finding_id == "INSTALLATION_TYPE_MISSING"


@pytest.mark.asyncio
async def test_unknown_installation_type_generates_warning() -> None:
    findings = await _check(
        {"installation_type": "Future Experimental Install"}
    )
    assert len(findings) == 1
    assert findings[0].finding_id == "INSTALLATION_TYPE_UNKNOWN"
