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
                    "home_assistant_version": context.system.get(
                        "home_assistant_version"
                    ),
                    "installation_type": context.system.get("installation_type"),
                    "supervisor_version": context.system.get("supervisor_version"),
                    "operating_system_version": context.system.get(
                        "operating_system_version"
                    ),
                    "frontend_version": context.system.get("frontend_version"),
                    "python_version": context.system.get("python_version"),
                    "python_implementation": context.system.get(
                        "python_implementation"
                    ),
                    "architecture": context.system.get("architecture"),
                    "platform": context.system.get("platform"),
                    "platform_release": context.system.get("platform_release"),
                    "os_name": context.system.get("os_name"),
                    "os_version": context.system.get("os_version"),
                    "docker": context.system.get("docker"),
                    "hassio": context.system.get("hassio"),
                    "timezone": context.system.get("timezone"),
                    "country": context.system.get("country"),
                },
            )
        ]


class SupervisorAvailabilityRule(BaseRule):
    """Detect a missing Supervisor where the installation normally includes it."""

    rule_id = "SUPERVISOR_AVAILABILITY"

    supervised_installation_types = {
        "Home Assistant OS",
        "Home Assistant Supervised",
    }

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        """Check whether Supervisor information is available when expected."""
        installation_type = context.system.get("installation_type")
        supervisor_version = context.system.get("supervisor_version")

        if installation_type not in self.supervised_installation_types:
            return []

        if isinstance(supervisor_version, str) and supervisor_version.strip():
            return []

        return [
            Finding(
                finding_id="SUPERVISOR_NOT_DETECTED",
                severity=Severity.WARNING,
                title="Supervisor not detected",
                description=(
                    "This installation type normally includes Home Assistant "
                    "Supervisor, but its version could not be detected."
                ),
                recommendation=(
                    "Verify that Supervisor is running correctly and that "
                    "the Supervisor update entity is available."
                ),
                data={
                    "installation_type": installation_type,
                    "supervisor_version": supervisor_version,
                },
            )
        ]
