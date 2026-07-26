"""Home Assistant Operating System version inspection rule."""

from __future__ import annotations

from ..context import InspectionContext
from ..models import Finding
from ..severity import Severity
from ..utils.versions import (
    VersionKind,
    parse_home_assistant_os_version,
)
from .base import BaseRule


class OperatingSystemVersionRule(BaseRule):
    """Report non-stable or invalid Home Assistant OS versions."""

    rule_id = "OPERATING_SYSTEM_VERSION"

    async def check(self, context: InspectionContext) -> list[Finding]:
        """Inspect the collected Home Assistant OS version."""
        version = context.system.get("operating_system_version")

        # Missing values are valid for Container and Core installations.
        # Installation-specific availability belongs to a separate rule.
        if version is None or (
            isinstance(version, str) and not version.strip()
        ):
            return []

        info = parse_home_assistant_os_version(version)

        if info.kind is VersionKind.STABLE:
            return []

        if info.kind is VersionKind.BETA:
            return [
                Finding(
                    finding_id="OPERATING_SYSTEM_VERSION_BETA",
                    severity=Severity.INFO,
                    title="Running a Home Assistant OS beta version",
                    description=(
                        f"Home Assistant OS {version} is a beta release and "
                        "may contain unfinished changes."
                    ),
                    recommendation=(
                        "Use a stable Home Assistant OS release when maximum "
                        "reliability is required."
                    ),
                    data={"operating_system_version": version},
                )
            ]

        if info.kind is VersionKind.RC:
            return [
                Finding(
                    finding_id=(
                        "OPERATING_SYSTEM_VERSION_RELEASE_CANDIDATE"
                    ),
                    severity=Severity.INFO,
                    title=(
                        "Running a Home Assistant OS release candidate"
                    ),
                    description=(
                        f"Home Assistant OS {version} is a release candidate "
                        "and may still contain unresolved issues."
                    ),
                    recommendation=(
                        "Use a stable Home Assistant OS release when maximum "
                        "reliability is required."
                    ),
                    data={"operating_system_version": version},
                )
            ]

        if info.kind is VersionKind.DEV:
            return [
                Finding(
                    finding_id="OPERATING_SYSTEM_VERSION_DEVELOPMENT",
                    severity=Severity.INFO,
                    title=(
                        "Running a Home Assistant OS development version"
                    ),
                    description=(
                        f"Home Assistant OS {version} is a development build "
                        "intended primarily for testing."
                    ),
                    recommendation=(
                        "Use a stable Home Assistant OS release unless this "
                        "installation is specifically intended for "
                        "development."
                    ),
                    data={"operating_system_version": version},
                )
            ]

        return [
            Finding(
                finding_id="OPERATING_SYSTEM_VERSION_UNKNOWN",
                severity=Severity.WARNING,
                title="Unable to determine Home Assistant OS version",
                description=(
                    "HA Inspector collected an operating system version but "
                    "could not interpret it as a valid Home Assistant OS "
                    "version."
                ),
                recommendation=(
                    "Review the collected system information and the Home "
                    "Assistant logs to verify the operating system version."
                ),
                data={"operating_system_version": version},
            )
        ]
