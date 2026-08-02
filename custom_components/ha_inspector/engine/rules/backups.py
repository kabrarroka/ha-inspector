"""Backup inspection rules for HA Inspector."""

from __future__ import annotations

from ..context import InspectionContext
from ..models import Finding
from ..severity import Severity
from .base import BaseRule


class BackupCountRule(BaseRule):
    """Detect installations with too few available backups."""

    rule_id = "BACKUP_COUNT"

    minimum_recommended = 3

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        """Report when fewer than three backups are available."""
        backups = context.backups

        if backups.get("available") is not True:
            return []

        count = backups.get("count")

        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            return []

        if count >= self.minimum_recommended:
            return []

        if count == 0:
            severity = Severity.ERROR
            finding_id = "BACKUP_COUNT_NONE"
            title = "No backups are available"
            description = (
                "Home Assistant does not currently report any available backups."
            )
        else:
            severity = Severity.WARNING
            finding_id = "BACKUP_COUNT_LOW"
            title = "Too few backups are available"
            description = (
                f"Home Assistant reports {count} available "
                f"{'backup' if count == 1 else 'backups'}; "
                f"at least {self.minimum_recommended} are recommended."
            )

        return [
            Finding(
                finding_id=finding_id,
                severity=severity,
                title=title,
                description=description,
                recommendation=(
                    "Create a new backup and keep multiple recent copies, "
                    "preferably including at least one copy outside the "
                    "Home Assistant device."
                ),
                data={
                    "backup_count": count,
                    "minimum_recommended": self.minimum_recommended,
                    "latest_backup": backups.get("latest"),
                    "oldest_backup": backups.get("oldest"),
                    "agent_error_count": backups.get(
                        "agent_error_count",
                        0,
                    ),
                },
            )
        ]
