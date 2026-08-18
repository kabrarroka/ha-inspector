import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.rules.system import (
    CpuLoadRule,
    SystemInformationRule,
)
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


@pytest.mark.asyncio
async def test_cpu_load_returns_nothing_when_unknown() -> None:
    context = InspectionContext(
        system=SystemState(
            cpu_percent=None,
        )
    )

    assert await CpuLoadRule().check(context) == []


@pytest.mark.asyncio
async def test_cpu_load_returns_nothing_when_acceptable() -> None:
    context = InspectionContext(
        system=SystemState(
            cpu_percent=85.0,
        )
    )

    assert await CpuLoadRule().check(context) == []


@pytest.mark.asyncio
async def test_cpu_load_reports_warning() -> None:
    context = InspectionContext(
        system=SystemState(
            cpu_percent=90.0,
            cpu_count_logical=4,
            load_1m=2.0,
            load_5m=1.5,
            load_15m=1.0,
        )
    )

    findings = await CpuLoadRule().check(context)

    assert len(findings) == 1
    finding = findings[0]

    assert finding.finding_id == "CPU_LOAD_HIGH"
    assert finding.severity is Severity.WARNING
    assert finding.data == {
        "cpu_percent": 90.0,
        "warning_threshold": 85.0,
        "error_threshold": 95.0,
        "cpu_count_logical": 4,
        "load_1m": 2.0,
        "load_5m": 1.5,
        "load_15m": 1.0,
    }


@pytest.mark.asyncio
async def test_cpu_load_reports_error() -> None:
    context = InspectionContext(
        system=SystemState(
            cpu_percent=96.0,
            cpu_count_logical=4,
            load_1m=3.5,
            load_5m=3.0,
            load_15m=2.5,
        )
    )

    findings = await CpuLoadRule().check(context)

    assert len(findings) == 1
    finding = findings[0]

    assert finding.finding_id == "CPU_LOAD_CRITICAL"
    assert finding.severity is Severity.ERROR
    assert finding.data["cpu_percent"] == 96.0
    assert finding.data["cpu_count_logical"] == 4
