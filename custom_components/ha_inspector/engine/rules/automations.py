"""Automation inspection rules for HA Inspector."""

from __future__ import annotations

from ..context import InspectionContext
from ..models import Finding
from ..severity import Severity
from .base import BaseRule


class DisabledAutomationsRule(BaseRule):
    """Detect automation entities disabled in the entity registry."""

    rule_id = "DISABLED_AUTOMATIONS"

    async def check(self, context: InspectionContext) -> list[Finding]:
        """Report automations disabled by the user or an integration."""
        automations = context.entities.disabled_automations
        if not automations:
            return []

        return [
            Finding(
                finding_id="DISABLED_AUTOMATIONS_FOUND",
                severity=Severity.INFO,
                title="Disabled automations detected",
                description=(
                    f"{len(automations)} automation entities are disabled in "
                    "the entity registry."
                ),
                recommendation=(
                    "Review them and either re-enable automations still required "
                    "or remove obsolete entries."
                ),
                data={
                    "disabled_automation_count": len(automations),
                    "automations": automations,
                },
            )
        ]
