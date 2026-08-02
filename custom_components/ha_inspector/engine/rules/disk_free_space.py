"""Disk free-space inspection rule."""

from __future__ import annotations

from ..context import InspectionContext
from ..models import Finding
from ..severity import Severity
from .base import BaseRule


class DiskFreeSpaceRule(BaseRule):
    """Report low free space on the Home Assistant storage."""

    rule_id = "DISK_FREE_SPACE"

    warning_threshold = 20.0
    error_threshold = 10.0

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        """Return a finding when free disk space is below a threshold."""
        storage = context.storage
        free_percent = storage.get("free_percent")

        if not isinstance(free_percent, (int, float)):
            return []

        free_percent = float(free_percent)

        if free_percent < 0.0 or free_percent > 100.0:
            return []

        if free_percent < self.error_threshold:
            severity = Severity.ERROR
            finding_id = "DISK_FREE_SPACE_CRITICAL"
            title = "Disk free space is critically low"
        elif free_percent < self.warning_threshold:
            severity = Severity.WARNING
            finding_id = "DISK_FREE_SPACE_LOW"
            title = "Disk free space is low"
        else:
            return []

        return [
            Finding(
                finding_id=finding_id,
                severity=severity,
                title=title,
                description=(
                    "The Home Assistant storage has only "
                    f"{free_percent:.2f}% free space remaining."
                ),
                recommendation=(
                    "Remove obsolete backups and unnecessary files, reduce "
                    "Recorder retention if appropriate, or expand the "
                    "available storage."
                ),
                data={
                    "total_bytes": storage.get("total_bytes"),
                    "used_bytes": storage.get("used_bytes"),
                    "free_bytes": storage.get("free_bytes"),
                    "free_percent": free_percent,
                    "warning_threshold": self.warning_threshold,
                    "error_threshold": self.error_threshold,
                },
            )
        ]
