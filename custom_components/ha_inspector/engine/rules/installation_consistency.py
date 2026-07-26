"""Installation type consistency inspection rule."""

from __future__ import annotations

from typing import Any

from ..context import InspectionContext
from ..models import Finding
from ..severity import Severity
from .base import BaseRule


def _has_value(value: Any) -> bool:
    """Return whether a collected value contains meaningful data."""
    return value is not None and (
        not isinstance(value, str) or bool(value.strip())
    )


def _normalize_installation_type(value: Any) -> str | None:
    """Normalize known Home Assistant installation type labels."""
    if not isinstance(value, str) or not value.strip():
        return None

    normalized = " ".join(
        value.strip().lower().replace("_", " ").replace("-", " ").split()
    )

    aliases = {
        "home assistant os": "haos",
        "ha os": "haos",
        "haos": "haos",
        "home assistant supervised": "supervised",
        "supervised": "supervised",
        "home assistant container": "container",
        "container": "container",
        "home assistant core": "core",
        "core": "core",
    }
    return aliases.get(normalized)


class InstallationConsistencyRule(BaseRule):
    """Check consistency between installation type and component data."""

    rule_id = "INSTALLATION_CONSISTENCY"

    async def check(self, context: InspectionContext) -> list[Finding]:
        """Inspect installation type, Supervisor and HAOS information."""
        system = context.system
        raw_type = system.get("installation_type")
        installation_type = _normalize_installation_type(raw_type)

        if raw_type is None or (
            isinstance(raw_type, str) and not raw_type.strip()
        ):
            return [
                Finding(
                    finding_id="INSTALLATION_TYPE_MISSING",
                    severity=Severity.WARNING,
                    title="Installation type is unavailable",
                    description=(
                        "HA Inspector could not determine the Home Assistant "
                        "installation type, so component consistency cannot "
                        "be fully evaluated."
                    ),
                    recommendation=(
                        "Review the system collector output and confirm that "
                        "Home Assistant exposes its installation type."
                    ),
                    data={"installation_type": raw_type},
                )
            ]

        if installation_type is None:
            return [
                Finding(
                    finding_id="INSTALLATION_TYPE_UNKNOWN",
                    severity=Severity.WARNING,
                    title="Installation type is not recognized",
                    description=(
                        f"HA Inspector does not recognize the installation "
                        f"type value {raw_type!r}."
                    ),
                    recommendation=(
                        "Verify the collected installation type and update "
                        "HA Inspector if Home Assistant introduced a new "
                        "installation method or label."
                    ),
                    data={"installation_type": raw_type},
                )
            ]

        supervisor_available = _has_value(
            system.get("supervisor_version")
        )
        os_available = _has_value(
            system.get("operating_system_version")
        )
        findings: list[Finding] = []

        if installation_type == "haos":
            if not os_available:
                findings.append(
                    Finding(
                        finding_id="HAOS_VERSION_MISSING",
                        severity=Severity.WARNING,
                        title="Home Assistant OS version is unavailable",
                        description=(
                            "The installation is reported as Home Assistant "
                            "OS, but no operating system version was "
                            "collected."
                        ),
                        recommendation=(
                            "Review Supervisor connectivity and the system "
                            "collector data."
                        ),
                        data={"installation_type": raw_type},
                    )
                )

            # Missing Supervisor is already reported by
            # SupervisorAvailabilityRule, so it is not duplicated here.
            return findings

        if installation_type == "supervised":
            if os_available:
                findings.append(
                    Finding(
                        finding_id="UNEXPECTED_HAOS_VERSION",
                        severity=Severity.INFO,
                        title="Unexpected Home Assistant OS version",
                        description=(
                            "The installation is reported as Supervised, but "
                            "a Home Assistant OS version was also collected."
                        ),
                        recommendation=(
                            "Verify the installation type and collector "
                            "mapping. A Supervised installation runs on a "
                            "user-managed host operating system."
                        ),
                        data={
                            "installation_type": raw_type,
                            "operating_system_version": system.get(
                                "operating_system_version"
                            ),
                        },
                    )
                )
            return findings

        if supervisor_available:
            findings.append(
                Finding(
                    finding_id="UNEXPECTED_SUPERVISOR",
                    severity=Severity.WARNING,
                    title="Unexpected Supervisor information",
                    description=(
                        f"The installation is reported as {raw_type}, but a "
                        "Supervisor version was collected."
                    ),
                    recommendation=(
                        "Verify the installation type and the source used by "
                        "the system collector."
                    ),
                    data={
                        "installation_type": raw_type,
                        "supervisor_version": system.get(
                            "supervisor_version"
                        ),
                    },
                )
            )

        if os_available:
            findings.append(
                Finding(
                    finding_id="UNEXPECTED_HAOS_VERSION",
                    severity=Severity.WARNING,
                    title="Unexpected Home Assistant OS information",
                    description=(
                        f"The installation is reported as {raw_type}, but a "
                        "Home Assistant OS version was collected."
                    ),
                    recommendation=(
                        "Verify the installation type and the source used by "
                        "the system collector."
                    ),
                    data={
                        "installation_type": raw_type,
                        "operating_system_version": system.get(
                            "operating_system_version"
                        ),
                    },
                )
            )

        return findings
