"""System log health rules for HA Inspector."""

from __future__ import annotations

from ..context import InspectionContext
from ..models import Finding
from ..severity import Severity
from .base import BaseRule


class LogHealthRule(BaseRule):
    """Check recent Home Assistant warnings and errors."""

    rule_id = "LOG_HEALTH"

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        """Check recent system log health."""
        logs = context.logs

        if not logs.available:
            return []

        findings: list[Finding] = []

        error_entries = logs.error_entries + logs.critical_entries
        error_occurrences = (
            logs.error_occurrences + logs.critical_occurrences
        )

        common_data = {
            "warning_entries": logs.warning_entries,
            "error_entries": logs.error_entries,
            "critical_entries": logs.critical_entries,
            "warning_occurrences": logs.warning_occurrences,
            "error_occurrences": logs.error_occurrences,
            "critical_occurrences": logs.critical_occurrences,
            "top_loggers": logs.top_loggers,
            "window_hours": 24,
        }

        if error_entries:
            findings.append(
                Finding(
                    finding_id="SYSTEM_LOG_ERRORS",
                    severity=Severity.ERROR,
                    title="Recent errors were found in the system log",
                    description=(
                        f"{error_entries} distinct error or critical log "
                        f"entries were recorded recently, representing "
                        f"{error_occurrences} occurrences."
                    ),
                    recommendation=(
                        "Review Home Assistant System Log and investigate "
                        "the most frequently reported loggers."
                    ),
                    data=common_data,
                )
            )

        if logs.warning_entries:
            findings.append(
                Finding(
                    finding_id="SYSTEM_LOG_WARNINGS",
                    severity=Severity.WARNING,
                    title="Recent warnings were found in the system log",
                    description=(
                        f"{logs.warning_entries} distinct warning log "
                        f"entries were recorded recently, representing "
                        f"{logs.warning_occurrences} occurrences."
                    ),
                    recommendation=(
                        "Review Home Assistant System Log and monitor "
                        "repeated warnings that may indicate degraded "
                        "operation."
                    ),
                    data=common_data,
                )
            )

        return findings
