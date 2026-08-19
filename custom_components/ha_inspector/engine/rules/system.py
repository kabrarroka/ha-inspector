"""System inspection rules for HA Inspector."""

from __future__ import annotations

from ..context import InspectionContext
from ..models import Finding
from ..severity import Severity
from .base import BaseRule


class SystemInformationRule(BaseRule):
    """Create an informational finding with system details."""

    rule_id = "SYSTEM_INFORMATION"

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        """Return general system information."""
        if not context.system:
            return [
                Finding(
                    finding_id="SYSTEM_INFORMATION_UNAVAILABLE",
                    severity=Severity.ERROR,
                    title="System information unavailable",
                    description=(
                        "HA Inspector could not collect general system "
                        "information."
                    ),
                    recommendation=(
                        "Review the Home Assistant logs for errors raised "
                        "by the system collector."
                    ),
                )
            ]

        return [
            Finding(
                finding_id="SYSTEM_INFORMATION",
                severity=Severity.INFO,
                title="System information collected",
                description=(
                    "HA Inspector successfully collected general information "
                    "about this Home Assistant installation."
                ),
                data={
                    "home_assistant_version": context.system.home_assistant_version,
                    "python_version": context.system.python_version,
                    "architecture": context.system.architecture,
                    "timezone": context.system.timezone,
                    "country": context.system.country,
                },
            )
        ]


class CpuLoadRule(BaseRule):
    """Check whether host CPU usage is excessively high."""

    rule_id = "CPU_LOAD"

    warning_threshold = 85.0
    error_threshold = 95.0

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        """Check host CPU usage."""
        system = context.system
        cpu_percent = system.cpu_percent

        if not isinstance(cpu_percent, int | float):
            return []

        data = {
            "cpu_percent": cpu_percent,
            "warning_threshold": self.warning_threshold,
            "error_threshold": self.error_threshold,
            "cpu_count_logical": system.cpu_count_logical,
            "load_1m": system.load_1m,
            "load_5m": system.load_5m,
            "load_15m": system.load_15m,
        }

        if cpu_percent > self.error_threshold:
            return [
                Finding(
                    finding_id="CPU_LOAD_CRITICAL",
                    severity=Severity.ERROR,
                    title="CPU usage is critically high",
                    description=(
                        f"Host CPU usage is currently {cpu_percent:.1f}%."
                    ),
                    recommendation=(
                        "Review active integrations, automations and other "
                        "processes that may be consuming excessive CPU."
                    ),
                    data=data,
                )
            ]

        if cpu_percent > self.warning_threshold:
            return [
                Finding(
                    finding_id="CPU_LOAD_HIGH",
                    severity=Severity.WARNING,
                    title="CPU usage is high",
                    description=(
                        f"Host CPU usage is currently {cpu_percent:.1f}%."
                    ),
                    recommendation=(
                        "Monitor CPU usage and review resource-intensive "
                        "integrations or automations if the load remains high."
                    ),
                    data=data,
                )
            ]

        return []


class MemoryUsageRule(BaseRule):
    """Check whether host memory usage is excessively high."""

    rule_id = "MEMORY_USAGE"

    warning_threshold = 85.0
    error_threshold = 95.0

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        """Check host memory usage."""
        system = context.system
        memory_percent = system.memory_percent

        if not isinstance(memory_percent, int | float):
            return []

        data = {
            "memory_percent": memory_percent,
            "warning_threshold": self.warning_threshold,
            "error_threshold": self.error_threshold,
            "memory_total_bytes": system.memory_total_bytes,
            "memory_available_bytes": system.memory_available_bytes,
            "memory_used_bytes": system.memory_used_bytes,
        }

        if memory_percent > self.error_threshold:
            return [
                Finding(
                    finding_id="MEMORY_USAGE_CRITICAL",
                    severity=Severity.ERROR,
                    title="Memory usage is critically high",
                    description=(
                        f"Host memory usage is currently {memory_percent:.1f}%."
                    ),
                    recommendation=(
                        "Review integrations, add-ons and other processes "
                        "that may be consuming excessive memory."
                    ),
                    data=data,
                )
            ]

        if memory_percent > self.warning_threshold:
            return [
                Finding(
                    finding_id="MEMORY_USAGE_HIGH",
                    severity=Severity.WARNING,
                    title="Memory usage is high",
                    description=(
                        f"Host memory usage is currently {memory_percent:.1f}%."
                    ),
                    recommendation=(
                        "Monitor memory usage and review resource-intensive "
                        "integrations or add-ons if usage remains high."
                    ),
                    data=data,
                )
            ]

        return []


class RestartFrequencyRule(BaseRule):
    """Check whether Home Assistant is restarting too frequently."""

    rule_id = "RESTART_FREQUENCY"

    warning_threshold_24h = 3
    error_threshold_24h = 5

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        """Check recent Home Assistant restart frequency."""
        system = context.system
        restart_count_24h = system.restart_count_24h

        if not isinstance(restart_count_24h, int):
            return []

        data = {
            "restart_count_24h": restart_count_24h,
            "restart_count_7d": system.restart_count_7d,
            "warning_threshold_24h": self.warning_threshold_24h,
            "error_threshold_24h": self.error_threshold_24h,
        }

        if restart_count_24h >= self.error_threshold_24h:
            return [
                Finding(
                    finding_id="RESTART_FREQUENCY_CRITICAL",
                    severity=Severity.ERROR,
                    title="Home Assistant is restarting very frequently",
                    description=(
                        "Home Assistant has restarted "
                        f"{restart_count_24h} times in the last 24 hours."
                    ),
                    recommendation=(
                        "Review Home Assistant logs, recent updates, "
                        "integration failures and host stability to identify "
                        "the cause of repeated restarts."
                    ),
                    data=data,
                )
            ]

        if restart_count_24h >= self.warning_threshold_24h:
            return [
                Finding(
                    finding_id="RESTART_FREQUENCY_HIGH",
                    severity=Severity.WARNING,
                    title="Home Assistant is restarting frequently",
                    description=(
                        "Home Assistant has restarted "
                        f"{restart_count_24h} times in the last 24 hours."
                    ),
                    recommendation=(
                        "Monitor subsequent restarts and review logs for "
                        "shutdowns, crashes or watchdog activity."
                    ),
                    data=data,
                )
            ]

        return []
