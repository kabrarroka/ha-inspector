"""Supervisor add-on health rules for HA Inspector."""

from __future__ import annotations

from ..context import InspectionContext
from ..models import Finding
from ..severity import Severity
from .base import BaseRule


class AddonHealthRule(BaseRule):
    """Inspect abnormal Supervisor add-on states."""

    rule_id = "ADDON_HEALTH"

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        """Check Supervisor add-on health."""
        addons = context.addons

        if not addons.available:
            return []

        findings: list[Finding] = []

        error_addons = [
            addon
            for addon in addons.problematic
            if addon.get("state") == "error"
        ]

        unknown_addons = [
            addon
            for addon in addons.problematic
            if addon.get("state") == "unknown"
        ]

        common_data = {
            "total": addons.total,
            "started": addons.started,
            "startup": addons.startup,
            "stopped": addons.stopped,
            "unknown": addons.unknown,
            "error": addons.error,
            "updates_available": addons.updates_available,
        }

        if error_addons:
            findings.append(
                Finding(
                    finding_id="ADDON_STATE_ERROR",
                    severity=Severity.ERROR,
                    title="Add-ons are reporting an error state",
                    description=(
                        f"{len(error_addons)} installed add-on(s) are "
                        "currently reporting an error state."
                    ),
                    recommendation=(
                        "Review the affected add-ons in Home Assistant, "
                        "inspect their logs and verify their configuration "
                        "before restarting them."
                    ),
                    data={
                        **common_data,
                        "addons": error_addons,
                    },
                )
            )

        if unknown_addons:
            findings.append(
                Finding(
                    finding_id="ADDON_STATE_UNKNOWN",
                    severity=Severity.WARNING,
                    title="Add-ons have an unknown state",
                    description=(
                        f"{len(unknown_addons)} installed add-on(s) have "
                        "an unknown Supervisor state."
                    ),
                    recommendation=(
                        "Check Supervisor status and review the affected "
                        "add-ons if the unknown state persists."
                    ),
                    data={
                        **common_data,
                        "addons": unknown_addons,
                    },
                )
            )

        return findings
