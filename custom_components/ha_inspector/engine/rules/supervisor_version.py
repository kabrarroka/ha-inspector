"""Home Assistant Supervisor version inspection rule."""

from __future__ import annotations

from ..context import InspectionContext
from ..models import Finding
from ..severity import Severity
from ..utils.versions import VersionKind, parse_home_assistant_version
from .base import BaseRule


class SupervisorVersionRule(BaseRule):
    """Report non-stable or invalid Home Assistant Supervisor versions."""

    rule_id = "SUPERVISOR_VERSION"

    async def check(self, context: InspectionContext) -> list[Finding]:
        """Inspect the collected Home Assistant Supervisor version."""
        version = context.system.get("supervisor_version")

        # SupervisorAvailabilityRule is responsible for reporting a missing
        # Supervisor when the installation type requires one.
        if version is None or (
            isinstance(version, str) and not version.strip()
        ):
            return []

        info = parse_home_assistant_version(version)

        if info.kind is VersionKind.STABLE:
            return []

        if info.kind is VersionKind.BETA:
            return [
                Finding(
                    finding_id="SUPERVISOR_VERSION_BETA",
                    severity=Severity.INFO,
                    title="Running a Supervisor beta version",
                    description=(
                        f"Home Assistant Supervisor {version} is a beta "
                        "release and may contain unfinished changes."
                    ),
                    recommendation=(
                        "Use a stable Supervisor release when maximum "
                        "reliability is required."
                    ),
                    data={"supervisor_version": version},
                )
            ]

        if info.kind is VersionKind.RC:
            return [
                Finding(
                    finding_id="SUPERVISOR_VERSION_RELEASE_CANDIDATE",
                    severity=Severity.INFO,
                    title="Running a Supervisor release candidate",
                    description=(
                        f"Home Assistant Supervisor {version} is a release "
                        "candidate and may still contain unresolved issues."
                    ),
                    recommendation=(
                        "Use a stable Supervisor release when maximum "
                        "reliability is required."
                    ),
                    data={"supervisor_version": version},
                )
            ]

        if info.kind is VersionKind.DEV:
            return [
                Finding(
                    finding_id="SUPERVISOR_VERSION_DEVELOPMENT",
                    severity=Severity.INFO,
                    title="Running a Supervisor development version",
                    description=(
                        f"Home Assistant Supervisor {version} is a "
                        "development build intended primarily for testing."
                    ),
                    recommendation=(
                        "Use a stable Supervisor release unless this "
                        "installation is specifically intended for "
                        "development."
                    ),
                    data={"supervisor_version": version},
                )
            ]

        return [
            Finding(
                finding_id="SUPERVISOR_VERSION_UNKNOWN",
                severity=Severity.WARNING,
                title="Unable to determine Supervisor version",
                description=(
                    "HA Inspector collected a Supervisor version value but "
                    "could not interpret it as a valid version."
                ),
                recommendation=(
                    "Review the collected system information and the Home "
                    "Assistant logs to verify the Supervisor version."
                ),
                data={"supervisor_version": version},
            )
        ]
