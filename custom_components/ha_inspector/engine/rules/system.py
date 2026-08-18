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
