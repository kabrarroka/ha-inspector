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

    def __init__(
        self,
        *,
        minimum_recommended: int = 3,
    ) -> None:
        """Initialize configurable backup-count threshold."""
        minimum_recommended = int(minimum_recommended)

        if minimum_recommended < 0:
            raise ValueError(
                "Backup count threshold must satisfy minimum_recommended >= 0"
            )

        self.minimum_recommended = minimum_recommended

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        """Report when fewer than three backups are available."""
        backups = context.backups

        if backups.available is not True:
            return []

        count = backups.count

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
                    "latest_backup": backups.latest,
                    "oldest_backup": backups.oldest,
                    "agent_error_count": backups.agent_error_count,
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

        if backups.available is not True:
            return []

        error_count = backups.agent_error_count
        error_ids = backups.agent_error_ids

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
                    "backup_count": backups.count,
                    "latest_backup": backups.latest,
                },
            )
        ]


class BackupRedundancyRule(BaseRule):
    """Detect when the newest backup is stored in too few locations."""

    rule_id = "BACKUP_REDUNDANCY"

    minimum_recommended_agents = 2

    def __init__(
        self,
        *,
        minimum_recommended_agents: int = 2,
    ) -> None:
        """Initialize configurable backup-redundancy threshold."""
        minimum_recommended_agents = int(minimum_recommended_agents)

        if minimum_recommended_agents < 0:
            raise ValueError(
                "Backup redundancy threshold must satisfy "
                "minimum_recommended_agents >= 0"
            )

        self.minimum_recommended_agents = minimum_recommended_agents

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        """Report when the latest backup is not stored redundantly."""
        backups = context.backups

        if backups.available is not True:
            return []

        count = backups.count
        agent_count = backups.latest_backup_agent_count
        agent_ids = backups.latest_backup_agent_ids

        if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
            return []

        if (
            not isinstance(agent_count, int)
            or isinstance(agent_count, bool)
            or agent_count < 0
            or not isinstance(agent_ids, list)
        ):
            return []

        normalized_ids = sorted(
            {
                agent_id.strip()
                for agent_id in agent_ids
                if isinstance(agent_id, str) and agent_id.strip()
            }
        )

        if agent_count >= self.minimum_recommended_agents:
            return []

        return [
            Finding(
                finding_id="BACKUP_REDUNDANCY_LOW",
                severity=Severity.WARNING,
                title="Latest backup is not stored redundantly",
                description=(
                    f"The newest backup is available from {agent_count} backup "
                    f"{'agent' if agent_count == 1 else 'agents'}; at least "
                    f"{self.minimum_recommended_agents} are recommended."
                ),
                recommendation=(
                    "Store the newest backup in at least two independent locations, "
                    "including one outside the Home Assistant device."
                ),
                data={
                    "latest_backup": backups.latest,
                    "latest_backup_agent_count": agent_count,
                    "latest_backup_agent_ids": normalized_ids,
                    "minimum_recommended_agents": self.minimum_recommended_agents,
                },
            )
        ]


class BackupIntegrityRule(BaseRule):
    """Detect incomplete content in the newest backup."""

    rule_id = "BACKUP_INTEGRITY"

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        """Report failed content or storage targets for the latest backup."""
        backups = context.backups

        if backups.available is not True:
            return []

        count = backups.count
        if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
            return []

        failed_addons = backups.latest_backup_failed_addons
        failed_folders = backups.latest_backup_failed_folders
        failed_agent_ids = backups.latest_backup_failed_agent_ids

        if not all(
            isinstance(value, list)
            for value in (
                failed_addons,
                failed_folders,
                failed_agent_ids,
            )
        ):
            return []

        normalized_addons = sorted(
            {
                value.strip()
                for value in failed_addons
                if isinstance(value, str) and value.strip()
            }
        )
        normalized_folders = sorted(
            {
                value.strip()
                for value in failed_folders
                if isinstance(value, str) and value.strip()
            }
        )
        normalized_agent_ids = sorted(
            {
                value.strip()
                for value in failed_agent_ids
                if isinstance(value, str) and value.strip()
            }
        )

        content_incomplete = bool(normalized_addons or normalized_folders)
        storage_incomplete = bool(normalized_agent_ids)

        if not content_incomplete and not storage_incomplete:
            return []

        if content_incomplete:
            severity = Severity.ERROR
            finding_id = "BACKUP_INTEGRITY_INCOMPLETE"
            title = "Latest backup contains incomplete content"
            description = (
                "Home Assistant reports that one or more requested components "
                "could not be included in the newest backup."
            )
        else:
            severity = Severity.WARNING
            finding_id = "BACKUP_INTEGRITY_AGENT_FAILURES"
            title = "Latest backup failed on some storage agents"
            description = (
                "The newest backup was created, but Home Assistant reports "
                "failures while writing it to one or more backup agents."
            )

        return [
            Finding(
                finding_id=finding_id,
                severity=severity,
                title=title,
                description=description,
                recommendation=(
                    "Review the failed components and backup agents, correct the "
                    "underlying errors, and create a new backup before relying on "
                    "the current recovery point."
                ),
                data={
                    "latest_backup": backups.latest,
                    "failed_addons": normalized_addons,
                    "failed_folders": normalized_folders,
                    "failed_agent_ids": normalized_agent_ids,
                    "content_incomplete": content_incomplete,
                    "storage_incomplete": storage_incomplete,
                },
            )
        ]

