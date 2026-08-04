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
class BackupAgentErrorsRule(BaseRule):
    """Detect backup agents that failed while listing backups."""

    rule_id = "BACKUP_AGENT_ERRORS"

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        """Report backup agents that returned errors."""
        backups = context.backups

        if backups.get("available") is not True:
            return []

        error_count = backups.get("agent_error_count")
        error_ids = backups.get("agent_error_ids")

        if (
            not isinstance(error_count, int)
            or isinstance(error_count, bool)
            or error_count <= 0
        ):
            return []

        if not isinstance(error_ids, list):
            return []

        normalized_ids = sorted(
            {
                agent_id.strip()
                for agent_id in error_ids
                if isinstance(agent_id, str) and agent_id.strip()
            }
        )

        return [
            Finding(
                finding_id="BACKUP_AGENT_ERRORS_FOUND",
                severity=Severity.WARNING,
                title="Backup agent errors detected",
                description=(
                    f"{error_count} backup "
                    f"{'agent returned' if error_count == 1 else 'agents returned'} "
                    "an error while Home Assistant was reading the backup inventory."
                ),
                recommendation=(
                    "Review the affected backup agents, verify their credentials "
                    "and connectivity, and confirm that remote backups are still "
                    "being created successfully."
                ),
                data={
                    "agent_error_count": error_count,
                    "agent_error_ids": normalized_ids,
                    "backup_count": backups.get("count"),
                    "latest_backup": backups.get("latest"),
                },
            )
        ]