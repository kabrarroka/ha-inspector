"""Home Assistant Core version inspection rule."""

from __future__ import annotations

from ..context import InspectionContext
from ..models import Finding
from ..severity import Severity
from ..utils.versions import VersionKind, parse_home_assistant_version
from .base import BaseRule


class CoreVersionRule(BaseRule):
    """Report non-stable or unavailable Home Assistant Core versions."""

    rule_id = "CORE_VERSION"

    async def check(self, context: InspectionContext) -> list[Finding]:
        """Inspect the collected Home Assistant Core version."""
        version = context.system.get("home_assistant_version")
        info = parse_home_assistant_version(version)

        if info.kind is VersionKind.STABLE:
            return []

        if info.kind is VersionKind.BETA:
            return [
                Finding(
                    finding_id="CORE_VERSION_BETA",
                    severity=Severity.INFO,
                    title="Running a beta version",
                    description=(
                        f"Home Assistant Core {version} is a beta release. "
                        "Beta versions may contain unfinished features or "
                        "unexpected behavior."
                    ),
                    recommendation=(
                        "Use a stable Home Assistant Core release for systems "
                        "where maximum reliability is required."
                    ),
                    data={"home_assistant_version": version},
                )
            ]

        if info.kind is VersionKind.RC:
            return [
                Finding(
                    finding_id="CORE_VERSION_RELEASE_CANDIDATE",
                    severity=Severity.INFO,
                    title="Running a release candidate",
                    description=(
                        f"Home Assistant Core {version} is a release candidate. "
                        "Release candidates are close to stable but may still "
                        "contain unresolved issues."
                    ),
                    recommendation=(
                        "Use a stable Home Assistant Core release for systems "
                        "where maximum reliability is required."
                    ),
                    data={"home_assistant_version": version},
                )
            ]

        if info.kind is VersionKind.DEV:
            return [
                Finding(
                    finding_id="CORE_VERSION_DEVELOPMENT",
                    severity=Severity.INFO,
                    title="Running a development version",
                    description=(
                        f"Home Assistant Core {version} is a development build. "
                        "Development builds are intended for testing and may be "
                        "unstable."
                    ),
                    recommendation=(
                        "Use a stable Home Assistant Core release unless this "
                        "installation is specifically intended for development."
                    ),
                    data={"home_assistant_version": version},
                )
            ]

        return [
            Finding(
                finding_id="CORE_VERSION_UNKNOWN",
                severity=Severity.WARNING,
                title="Unable to determine Core version",
                description=(
                    "HA Inspector could not determine a valid Home Assistant "
                    "Core version from the collected system information."
                ),
                recommendation=(
                    "Verify that the system collector can read the Home "
                    "Assistant Core version and review the Home Assistant logs."
                ),
                data={"home_assistant_version": version},
            )
        ]
