"""Config entry inspection rules for HA Inspector."""

from __future__ import annotations

from ..context import InspectionContext
from ..models import Finding
from ..severity import Severity
from .base import BaseRule


class IntegrationSetupErrorRule(BaseRule):
    """Detect integrations that failed to set up."""

    rule_id = "INTEGRATION_SETUP_ERRORS"

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        """Return findings for config entries in setup error."""
        entries = [
            entry
            for entry in context.integrations.get(
                "problematic_entries",
                [],
            )
            if entry.get("state") == "setup_error"
        ]

        if not entries:
            return []

        return [
            Finding(
                finding_id="INTEGRATION_SETUP_ERRORS",
                severity=Severity.ERROR,
                title="Integrations failed to set up",
                description=(
                    f"{len(entries)} integration configuration "
                    "entries failed during setup."
                ),
                recommendation=(
                    "Open Settings > Devices & services and review the "
                    "affected integrations. Also check the Home Assistant "
                    "logs for the original setup exception."
                ),
                data={
                    "count": len(entries),
                    "entries": entries,
                },
            )
        ]


class IntegrationSetupRetryRule(BaseRule):
    """Detect integrations waiting for an automatic retry."""

    rule_id = "INTEGRATION_SETUP_RETRIES"

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        """Return findings for config entries in setup retry."""
        entries = [
            entry
            for entry in context.integrations.get(
                "problematic_entries",
                [],
            )
            if entry.get("state") == "setup_retry"
        ]

        if not entries:
            return []

        return [
            Finding(
                finding_id="INTEGRATION_SETUP_RETRIES",
                severity=Severity.WARNING,
                title="Integrations are waiting to retry",
                description=(
                    f"{len(entries)} integration configuration "
                    "entries could not start and are waiting for an "
                    "automatic retry."
                ),
                recommendation=(
                    "Check connectivity, credentials and dependent "
                    "devices. Run HA Inspector again after Home Assistant "
                    "has retried the integrations."
                ),
                data={
                    "count": len(entries),
                    "entries": entries,
                },
            )
        ]


class IntegrationLifecycleErrorRule(BaseRule):
    """Detect migration and unload failures."""

    rule_id = "INTEGRATION_LIFECYCLE_ERRORS"

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        """Return findings for migration or unload errors."""
        affected_states = {
            "migration_error",
            "failed_unload",
        }

        entries = [
            entry
            for entry in context.integrations.get(
                "problematic_entries",
                [],
            )
            if entry.get("state") in affected_states
        ]

        if not entries:
            return []

        return [
            Finding(
                finding_id="INTEGRATION_LIFECYCLE_ERRORS",
                severity=Severity.ERROR,
                title="Integration lifecycle errors detected",
                description=(
                    f"{len(entries)} integration configuration "
                    "entries have migration or unloading errors."
                ),
                recommendation=(
                    "Review the affected integrations and the Home "
                    "Assistant logs. A restart may be required after "
                    "correcting the underlying error."
                ),
                data={
                    "count": len(entries),
                    "entries": entries,
                },
            )
        ]