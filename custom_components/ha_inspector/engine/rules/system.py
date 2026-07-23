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
                    "python_version": context.system.get("python_version"),
                    "architecture": context.system.get("architecture"),
                    "timezone": context.system.get("timezone"),
                    "country": context.system.get("country"),
                },
            )
        ]