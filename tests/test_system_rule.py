import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.rules.system import (
    CpuLoadRule,
    MemoryUsageRule,
    NetworkConnectivityRule,
    RestartFrequencyRule,
    SystemInformationRule,
    TimeSynchronizationRule,
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


@pytest.mark.asyncio
async def test_memory_usage_returns_nothing_when_unknown() -> None:
    context = InspectionContext(
        system=SystemState(memory_percent=None)
    )

    assert await MemoryUsageRule().check(context) == []


@pytest.mark.asyncio
async def test_memory_usage_returns_nothing_when_acceptable() -> None:
    context = InspectionContext(
        system=SystemState(memory_percent=85.0)
    )

    assert await MemoryUsageRule().check(context) == []


@pytest.mark.asyncio
async def test_memory_usage_reports_warning() -> None:
    context = InspectionContext(
        system=SystemState(
            memory_percent=90.0,
            memory_total_bytes=8_000,
            memory_available_bytes=800,
            memory_used_bytes=7_200,
        )
    )

    findings = await MemoryUsageRule().check(context)

    assert len(findings) == 1
    finding = findings[0]

    assert finding.finding_id == "MEMORY_USAGE_HIGH"
    assert finding.severity is Severity.WARNING
    assert finding.data == {
        "memory_percent": 90.0,
        "warning_threshold": 85.0,
        "error_threshold": 95.0,
        "memory_total_bytes": 8_000,
        "memory_available_bytes": 800,
        "memory_used_bytes": 7_200,
    }


@pytest.mark.asyncio
async def test_memory_usage_reports_error() -> None:
    context = InspectionContext(
        system=SystemState(
            memory_percent=96.0,
            memory_total_bytes=8_000,
            memory_available_bytes=320,
            memory_used_bytes=7_680,
        )
    )

    findings = await MemoryUsageRule().check(context)

    assert len(findings) == 1
    finding = findings[0]

    assert finding.finding_id == "MEMORY_USAGE_CRITICAL"
    assert finding.severity is Severity.ERROR
    assert finding.data["memory_percent"] == 96.0
    assert finding.data["memory_total_bytes"] == 8_000


@pytest.mark.asyncio
async def test_restart_frequency_returns_nothing_when_unknown() -> None:
    context = InspectionContext(
        system=SystemState(restart_count_24h=None)
    )

    assert await RestartFrequencyRule().check(context) == []


@pytest.mark.asyncio
async def test_restart_frequency_returns_nothing_when_acceptable() -> None:
    context = InspectionContext(
        system=SystemState(
            restart_count_24h=2,
            restart_count_7d=4,
        )
    )

    assert await RestartFrequencyRule().check(context) == []


@pytest.mark.asyncio
async def test_restart_frequency_reports_warning() -> None:
    context = InspectionContext(
        system=SystemState(
            restart_count_24h=3,
            restart_count_7d=6,
        )
    )

    findings = await RestartFrequencyRule().check(context)

    assert len(findings) == 1
    finding = findings[0]

    assert finding.finding_id == "RESTART_FREQUENCY_HIGH"
    assert finding.severity is Severity.WARNING
    assert finding.data["restart_count_24h"] == 3
    assert finding.data["restart_count_7d"] == 6


@pytest.mark.asyncio
async def test_restart_frequency_reports_error() -> None:
    context = InspectionContext(
        system=SystemState(
            restart_count_24h=5,
            restart_count_7d=9,
        )
    )

    findings = await RestartFrequencyRule().check(context)

    assert len(findings) == 1
    finding = findings[0]

    assert finding.finding_id == "RESTART_FREQUENCY_CRITICAL"
    assert finding.severity is Severity.ERROR
    assert finding.data["restart_count_24h"] == 5



@pytest.mark.asyncio
async def test_time_synchronization_unknown_returns_nothing() -> None:
    context = InspectionContext(
        system=SystemState(time_synchronized=None)
    )

    assert await TimeSynchronizationRule().check(context) == []


@pytest.mark.asyncio
async def test_time_synchronization_ok_returns_nothing() -> None:
    context = InspectionContext(
        system=SystemState(time_synchronized=True)
    )

    assert await TimeSynchronizationRule().check(context) == []


@pytest.mark.asyncio
async def test_time_synchronization_failure_reports_error() -> None:
    context = InspectionContext(
        system=SystemState(time_synchronized=False)
    )

    findings = await TimeSynchronizationRule().check(context)

    assert len(findings) == 1

    finding = findings[0]

    assert finding.finding_id == "TIME_SYNCHRONIZATION_FAILED"
    assert finding.severity is Severity.ERROR
    assert finding.data == {
        "time_synchronized": False,
    }



@pytest.mark.asyncio
async def test_network_connectivity_unknown_returns_nothing() -> None:
    context = InspectionContext(
        system=SystemState(
            dns_resolution_ok=None,
            host_internet=None,
            supervisor_internet=None,
        )
    )

    assert await NetworkConnectivityRule().check(context) == []


@pytest.mark.asyncio
async def test_network_connectivity_healthy_returns_nothing() -> None:
    context = InspectionContext(
        system=SystemState(
            dns_resolution_ok=True,
            host_internet=True,
            supervisor_internet=True,
        )
    )

    assert await NetworkConnectivityRule().check(context) == []


@pytest.mark.asyncio
async def test_network_connectivity_reports_dns_failure() -> None:
    context = InspectionContext(
        system=SystemState(
            dns_resolution_ok=False,
            host_internet=True,
            supervisor_internet=True,
        )
    )

    findings = await NetworkConnectivityRule().check(context)

    assert len(findings) == 1
    assert findings[0].finding_id == "DNS_RESOLUTION_FAILED"
    assert findings[0].severity is Severity.ERROR


@pytest.mark.asyncio
async def test_network_connectivity_reports_host_failure() -> None:
    context = InspectionContext(
        system=SystemState(
            dns_resolution_ok=True,
            host_internet=False,
            supervisor_internet=False,
        )
    )

    findings = await NetworkConnectivityRule().check(context)

    assert len(findings) == 1
    assert findings[0].finding_id == "HOST_INTERNET_UNAVAILABLE"
    assert findings[0].severity is Severity.ERROR


@pytest.mark.asyncio
async def test_network_connectivity_reports_supervisor_failure() -> None:
    context = InspectionContext(
        system=SystemState(
            dns_resolution_ok=True,
            host_internet=True,
            supervisor_internet=False,
        )
    )

    findings = await NetworkConnectivityRule().check(context)

    assert len(findings) == 1
    assert findings[0].finding_id == "SUPERVISOR_INTERNET_UNAVAILABLE"
    assert findings[0].severity is Severity.WARNING


@pytest.mark.asyncio
async def test_network_connectivity_can_report_multiple_failures() -> None:
    context = InspectionContext(
        system=SystemState(
            dns_resolution_ok=False,
            host_internet=False,
            supervisor_internet=False,
        )
    )

    findings = await NetworkConnectivityRule().check(context)

    assert {
        finding.finding_id
        for finding in findings
    } == {
        "DNS_RESOLUTION_FAILED",
        "HOST_INTERNET_UNAVAILABLE",
    }



def test_cpu_load_default_thresholds() -> None:
    """CPU load preserves backward-compatible default thresholds."""
    rule = CpuLoadRule()

    assert rule.warning_threshold == 85.0
    assert rule.error_threshold == 95.0


@pytest.mark.asyncio
async def test_cpu_load_custom_thresholds() -> None:
    """Configured CPU thresholds control finding severity."""
    context = InspectionContext(
        system=SystemState(cpu_percent=71.0)
    )
    rule = CpuLoadRule(
        warning_threshold=70.0,
        error_threshold=80.0,
    )

    findings = await rule.check(context)

    assert len(findings) == 1
    assert findings[0].finding_id == "CPU_LOAD_HIGH"
    assert findings[0].severity is Severity.WARNING
    assert findings[0].data["warning_threshold"] == 70.0
    assert findings[0].data["error_threshold"] == 80.0


def test_cpu_load_accepts_boundary_thresholds() -> None:
    """CPU thresholds may span the complete percentage range."""
    rule = CpuLoadRule(
        warning_threshold=0.0,
        error_threshold=100.0,
    )

    assert rule.warning_threshold == 0.0
    assert rule.error_threshold == 100.0


@pytest.mark.parametrize(
    ("warning_threshold", "error_threshold"),
    [
        (-1.0, 95.0),
        (85.0, 101.0),
        (96.0, 95.0),
    ],
)
def test_cpu_load_rejects_invalid_thresholds(
    warning_threshold: float,
    error_threshold: float,
) -> None:
    """Invalid CPU threshold ranges are rejected."""
    with pytest.raises(ValueError, match="CPU load thresholds"):
        CpuLoadRule(
            warning_threshold=warning_threshold,
            error_threshold=error_threshold,
        )


def test_memory_usage_default_thresholds() -> None:
    """Memory usage preserves backward-compatible default thresholds."""
    rule = MemoryUsageRule()

    assert rule.warning_threshold == 85.0
    assert rule.error_threshold == 95.0


@pytest.mark.asyncio
async def test_memory_usage_custom_thresholds() -> None:
    """Configured memory thresholds control finding severity."""
    context = InspectionContext(
        system=SystemState(memory_percent=76.0)
    )
    rule = MemoryUsageRule(
        warning_threshold=75.0,
        error_threshold=90.0,
    )

    findings = await rule.check(context)

    assert len(findings) == 1
    assert findings[0].finding_id == "MEMORY_USAGE_HIGH"
    assert findings[0].severity is Severity.WARNING
    assert findings[0].data["warning_threshold"] == 75.0
    assert findings[0].data["error_threshold"] == 90.0


def test_memory_usage_accepts_boundary_thresholds() -> None:
    """Memory thresholds may span the complete percentage range."""
    rule = MemoryUsageRule(
        warning_threshold=0.0,
        error_threshold=100.0,
    )

    assert rule.warning_threshold == 0.0
    assert rule.error_threshold == 100.0


@pytest.mark.parametrize(
    ("warning_threshold", "error_threshold"),
    [
        (-1.0, 95.0),
        (85.0, 101.0),
        (96.0, 95.0),
    ],
)
def test_memory_usage_rejects_invalid_thresholds(
    warning_threshold: float,
    error_threshold: float,
) -> None:
    """Invalid memory threshold ranges are rejected."""
    with pytest.raises(ValueError, match="Memory usage thresholds"):
        MemoryUsageRule(
            warning_threshold=warning_threshold,
            error_threshold=error_threshold,
        )


def test_restart_frequency_default_thresholds() -> None:
    """Restart frequency preserves backward-compatible defaults."""
    rule = RestartFrequencyRule()

    assert rule.warning_threshold_24h == 3
    assert rule.error_threshold_24h == 5


@pytest.mark.asyncio
async def test_restart_frequency_custom_thresholds() -> None:
    """Configured restart thresholds control finding severity."""
    context = InspectionContext(
        system=SystemState(
            restart_count_24h=4,
            restart_count_7d=8,
        )
    )
    rule = RestartFrequencyRule(
        warning_threshold_24h=4,
        error_threshold_24h=7,
    )

    findings = await rule.check(context)

    assert len(findings) == 1
    assert findings[0].finding_id == "RESTART_FREQUENCY_HIGH"
    assert findings[0].severity is Severity.WARNING
    assert findings[0].data["warning_threshold_24h"] == 4
    assert findings[0].data["error_threshold_24h"] == 7


def test_restart_frequency_accepts_boundary_thresholds() -> None:
    """Zero and equal restart thresholds are valid."""
    rule = RestartFrequencyRule(
        warning_threshold_24h=0,
        error_threshold_24h=0,
    )

    assert rule.warning_threshold_24h == 0
    assert rule.error_threshold_24h == 0


@pytest.mark.parametrize(
    ("warning_threshold_24h", "error_threshold_24h"),
    [
        (-1, 5),
        (3, -1),
        (6, 5),
    ],
)
def test_restart_frequency_rejects_invalid_thresholds(
    warning_threshold_24h: int,
    error_threshold_24h: int,
) -> None:
    """Invalid restart-frequency threshold ranges are rejected."""
    with pytest.raises(ValueError, match="Restart-frequency thresholds"):
        RestartFrequencyRule(
            warning_threshold_24h=warning_threshold_24h,
            error_threshold_24h=error_threshold_24h,
        )
