"""Backup age inspection rule for HA Inspector."""

from __future__ import annotations

from datetime import UTC, datetime

from ..context import InspectionContext
from ..models import Finding
from ..severity import Severity
from .base import BaseRule


class BackupAgeRule(BaseRule):
    """Detect when the newest available backup is too old."""

    rule_id = "BACKUP_AGE"

    warning_age_days = 7
    error_age_days = 30

    def _now(self) -> datetime:
        """Return the current UTC time."""
        return datetime.now(UTC)

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        """Report when the newest backup exceeds the age thresholds."""
        backups = context.backups

        if backups.get("available") is not True:
            return []

        latest = backups.get("latest")

        if not isinstance(latest, str) or not latest.strip():
            return []

        try:
            latest_at = datetime.fromisoformat(latest)
        except ValueError:
            return []

        if latest_at.tzinfo is None:
            return []

        latest_at_utc = latest_at.astimezone(UTC)
        age_seconds = (self._now() - latest_at_utc).total_seconds()

        if age_seconds < 0:
            return []

        age_days = int(age_seconds // 86400)

        if age_days >= self.error_age_days:
            severity = Severity.ERROR
            finding_id = "BACKUP_AGE_CRITICAL"
            title = "The newest backup is too old"
        elif age_days >= self.warning_age_days:
            severity = Severity.WARNING
            finding_id = "BACKUP_AGE_HIGH"
            title = "The newest backup is becoming old"
        else:
            return []

        return [
            Finding(
                finding_id=finding_id,
                severity=severity,
                title=title,
                description=(
                    "The newest available Home Assistant backup is "
                    f"{age_days} days old."
                ),
                recommendation=(
                    "Create a new backup and verify that scheduled backups "
                    "are running correctly."
                ),
                data={
                    "latest_backup": latest_at_utc.isoformat(),
                    "backup_age_days": age_days,
                    "warning_age_days": self.warning_age_days,
                    "error_age_days": self.error_age_days,
                    "backup_count": backups.get("count"),
                },
            )
        ]