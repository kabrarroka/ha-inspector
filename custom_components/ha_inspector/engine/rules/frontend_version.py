"""Home Assistant Frontend version inspection rule."""

from __future__ import annotations

from ..context import InspectionContext
from ..models import Finding
from ..severity import Severity
from ..utils.versions import (
    VersionKind,
    parse_home_assistant_frontend_version,
)
from .base import BaseRule


class FrontendVersionRule(BaseRule):
    """Validate the collected Home Assistant Frontend version."""

    rule_id = "FRONTEND_VERSION"

    async def check(self, context: InspectionContext) -> list[Finding]:
        """Inspect the collected Home Assistant Frontend version."""
        version = context.system.get("frontend_version")

        # A missing value may reflect an unavailable data source. A separate
        # availability rule can decide later whether that should be reported.
        if version is None or (
            isinstance(version, str) and not version.strip()
        ):
            return []

        info = parse_home_assistant_frontend_version(version)

        if info.kind is VersionKind.STABLE:
            return []

        return [
            Finding(
                finding_id="FRONTEND_VERSION_UNKNOWN",
                severity=Severity.WARNING,
                title="Unable to determine Frontend version",
                description=(
                    "HA Inspector collected a Frontend version value but "
                    "could not interpret it as a valid date-based Frontend "
                    "version."
                ),
                recommendation=(
                    "Review the collected system information and verify the "
                    "Frontend version reported by Home Assistant."
                ),
                data={"frontend_version": version},
            )
        ]
