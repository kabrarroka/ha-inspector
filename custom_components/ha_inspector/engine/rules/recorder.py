"""Recorder inspection rules for HA Inspector."""

from __future__ import annotations

from ..context import InspectionContext
from ..models import Finding
from ..severity import Severity
from .base import BaseRule


class RecorderAvailabilityRule(BaseRule):
    """Check whether the recorder is available and operational."""

    rule_id = "RECORDER_AVAILABILITY"

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        """Check recorder availability."""
        recorder = context.recorder

        if recorder.get("available") is not True:
            return [
                Finding(
                    finding_id="RECORDER_UNAVAILABLE",
                    severity=Severity.ERROR,
                    title="Recorder is unavailable",
                    description=(
                        "HA Inspector could not access the Home Assistant "
                        "recorder instance."
                    ),
                    recommendation=(
                        "Check that Recorder is loaded and review the "
                        "Home Assistant logs for recorder errors."
                    ),
                )
            ]

        if not recorder.get("database_connected"):
            return [
                Finding(
                    finding_id="RECORDER_DATABASE_NOT_CONNECTED",
                    severity=Severity.ERROR,
                    title="Recorder database is not connected",
                    description=(
                        "Recorder is loaded, but its database connection "
                        "is not currently available."
                    ),
                    recommendation=(
                        "Review the Recorder and database errors in the "
                        "Home Assistant logs."
                    ),
                    data={
                        "database_dialect": recorder.get(
                            "database_dialect"
                        ),
                    },
                )
            ]

        if not recorder.get("database_ready"):
            return [
                Finding(
                    finding_id="RECORDER_DATABASE_NOT_READY",
                    severity=Severity.WARNING,
                    title="Recorder database is not ready",
                    description=(
                        "Recorder is connected, but the database is not "
                        "yet ready for normal operation."
                    ),
                    recommendation=(
                        "Wait for database initialization or migration to "
                        "finish and run the inspection again."
                    ),
                    data={
                        "migration_in_progress": recorder.get(
                            "migration_in_progress"
                        ),
                    },
                )
            ]

        return []


class RecorderKeepDaysRule(BaseRule):
    """Check the Recorder history retention period."""

    rule_id = "RECORDER_KEEP_DAYS"

    warning_threshold = 30
    error_threshold = 90

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        """Check whether Recorder retention may be excessive."""
        recorder = context.recorder

        if recorder.get("available") is not True:
            return []

        keep_days = recorder.get("keep_days")

        if not isinstance(keep_days, int):
            return [
                Finding(
                    finding_id="RECORDER_KEEP_DAYS_UNKNOWN",
                    severity=Severity.WARNING,
                    title="Recorder retention is unknown",
                    description=(
                        "HA Inspector could not determine the Recorder "
                        "history retention period."
                    ),
                )
            ]

        if keep_days > self.error_threshold:
            return [
                Finding(
                    finding_id="RECORDER_KEEP_DAYS_EXCESSIVE",
                    severity=Severity.ERROR,
                    title="Recorder retention is very high",
                    description=(
                        f"Recorder is configured to retain detailed history "
                        f"for {keep_days} days."
                    ),
                    recommendation=(
                        "Consider reducing purge_keep_days unless this long "
                        "retention period is intentional and the database "
                        "has sufficient storage and performance."
                    ),
                    data={
                        "keep_days": keep_days,
                        "warning_threshold": self.warning_threshold,
                        "error_threshold": self.error_threshold,
                    },
                )
            ]

        if keep_days > self.warning_threshold:
            return [
                Finding(
                    finding_id="RECORDER_KEEP_DAYS_HIGH",
                    severity=Severity.WARNING,
                    title="Recorder retention is high",
                    description=(
                        f"Recorder is configured to retain detailed history "
                        f"for {keep_days} days."
                    ),
                    recommendation=(
                        "Review whether this retention period is necessary. "
                        "Long retention can increase database size and "
                        "maintenance time."
                    ),
                    data={
                        "keep_days": keep_days,
                        "warning_threshold": self.warning_threshold,
                    },
                )
            ]

        return []