"""Tests for system inspection rules."""

from __future__ import annotations

import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.rules.system import (
    SupervisorAvailabilityRule,
    SystemInformationRule,
)
from custom_components.ha_inspector.engine.severity import Severity


@pytest.mark.asyncio
async def test_system_information_rule_returns_extended_inventory() -> None:
    """The system finding exposes installation and component versions."""
    context = InspectionContext()
    context.system.update(
        {
            "home_assistant_version": "2026.7.2",
            "installation_type": "Home Assistant OS",
            "supervisor_version": "2026.07.3",
            "operating_system_version": "18.1",
            "frontend_version": "20260624.5",
            "python_version": "3.13.5",
            "python_implementation": "CPython",
            "architecture": "x86_64",
            "platform": "Linux",
            "platform_release": "6.12.0",
            "os_name": "Linux",
            "os_version": "6.12.0",
            "docker": True,
            "hassio": True,
            "timezone": "Europe/Madrid",
            "country": "ES",
        }
    )

    findings = await SystemInformationRule().check(context)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.finding_id == "SYSTEM_INFORMATION"
    assert finding.severity is Severity.INFO
    assert finding.data["installation_type"] == "Home Assistant OS"
    assert finding.data["supervisor_version"] == "2026.07.3"
    assert finding.data["operating_system_version"] == "18.1"
    assert finding.data["frontend_version"] == "20260624.5"


@pytest.mark.asyncio
async def test_system_information_rule_supports_installations_without_supervisor() -> None:
    """Supervisor and HAOS versions may be absent outside HA OS."""
    context = InspectionContext()
    context.system.update(
        {
            "home_assistant_version": "2026.7.2",
            "installation_type": "Home Assistant Container",
            "supervisor_version": None,
            "operating_system_version": None,
            "frontend_version": "20260624.5",
        }
    )

    findings = await SystemInformationRule().check(context)

    assert len(findings) == 1
    assert findings[0].severity is Severity.INFO
    assert findings[0].data["supervisor_version"] is None
    assert findings[0].data["operating_system_version"] is None


@pytest.mark.asyncio
async def test_system_information_rule_reports_missing_context() -> None:
    """An empty context produces an error finding."""
    findings = await SystemInformationRule().check(InspectionContext())

    assert len(findings) == 1
    assert findings[0].finding_id == "SYSTEM_INFORMATION_UNAVAILABLE"
    assert findings[0].severity is Severity.ERROR


@pytest.mark.asyncio
async def test_supervisor_available_on_home_assistant_os() -> None:
    """HA OS with a detected Supervisor does not produce a finding."""
    context = InspectionContext()
    context.system.update(
        {
            "installation_type": "Home Assistant OS",
            "supervisor_version": "2026.07.3",
        }
    )

    findings = await SupervisorAvailabilityRule().check(context)

    assert findings == []


@pytest.mark.asyncio
async def test_supervisor_missing_on_home_assistant_os() -> None:
    """HA OS without a detected Supervisor produces a warning."""
    context = InspectionContext()
    context.system.update(
        {
            "installation_type": "Home Assistant OS",
            "supervisor_version": None,
        }
    )

    findings = await SupervisorAvailabilityRule().check(context)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.finding_id == "SUPERVISOR_NOT_DETECTED"
    assert finding.severity is Severity.WARNING
    assert finding.data["installation_type"] == "Home Assistant OS"


@pytest.mark.asyncio
async def test_supervisor_missing_on_container_is_expected() -> None:
    """Container installations do not require Supervisor."""
    context = InspectionContext()
    context.system.update(
        {
            "installation_type": "Home Assistant Container",
            "supervisor_version": None,
        }
    )

    findings = await SupervisorAvailabilityRule().check(context)

    assert findings == []


@pytest.mark.asyncio
async def test_supervisor_missing_on_supervised_installation() -> None:
    """A supervised installation without Supervisor data produces a warning."""
    context = InspectionContext()
    context.system.update(
        {
            "installation_type": "Home Assistant Supervised",
            "supervisor_version": "",
        }
    )

    findings = await SupervisorAvailabilityRule().check(context)

    assert len(findings) == 1
    assert findings[0].severity is Severity.WARNING
