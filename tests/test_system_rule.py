import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.rules.system import SystemInformationRule
from custom_components.ha_inspector.engine.severity import Severity
from custom_components.ha_inspector.engine.system_state import SystemState


@pytest.mark.asyncio
async def test_system_information_rule_reports_unavailable() -> None:
    context = InspectionContext(
        system=None,
    )

    findings = await SystemInformationRule().check(context)

    assert len(findings) == 1

    finding = findings[0]

    assert finding.finding_id == "SYSTEM_INFORMATION_UNAVAILABLE"
    assert finding.severity is Severity.ERROR
    assert finding.title == "System information unavailable"


@pytest.mark.asyncio
async def test_system_information_rule_reports_collected_information() -> None:
    context = InspectionContext(
        system=SystemState(
            home_assistant_version="2026.8.0",
            python_version="3.14.7",
            architecture="x86_64",
            timezone="Europe/Madrid",
            country="ES",
        )
    )

    findings = await SystemInformationRule().check(context)

    assert len(findings) == 1

    finding = findings[0]

    assert finding.finding_id == "SYSTEM_INFORMATION"
    assert finding.severity is Severity.INFO
    assert finding.title == "System information collected"
    assert finding.data == {
        "home_assistant_version": "2026.8.0",
        "python_version": "3.14.7",
        "architecture": "x86_64",
        "timezone": "Europe/Madrid",
        "country": "ES",
    }