"""Detect finding changes between historical inspections."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .severity import Severity


@dataclass(frozen=True, slots=True)
class FindingDeltas:
    """Finding changes between two comparable inspections."""

    added: tuple[dict[str, str], ...]
    resolved: tuple[dict[str, str], ...]
    persistent: tuple[dict[str, str], ...]
    severity_changed: tuple[dict[str, str], ...]

    def as_dict(self) -> dict[str, list[dict[str, str]]]:
        """Return a JSON-serializable comparison."""
        return {
            "added": list(self.added),
            "resolved": list(self.resolved),
            "persistent": list(self.persistent),
            "severity_changed": list(self.severity_changed),
        }


def compare_finding_deltas(
    previous: dict[str, Any],
    current: dict[str, Any],
) -> FindingDeltas | None:
    """Compare findings from two complete, compatible inspections."""
    if (
        not isinstance(previous.get("inspection_scope"), str)
        or not previous["inspection_scope"]
        or previous["inspection_scope"] != current.get("inspection_scope")
        or (
            previous.get("profile") is not None
            and (
                not isinstance(previous["profile"], str)
                or not previous["profile"]
            )
        )
        or previous.get("profile") != current.get("profile")
        or type(previous.get("collectors_failed")) is not int
        or previous["collectors_failed"] != 0
        or type(current.get("collectors_failed")) is not int
        or current["collectors_failed"] != 0
    ):
        return None

    previous_findings = previous.get("findings")
    current_findings = current.get("findings")

    if not isinstance(previous_findings, list) or not isinstance(
        current_findings, list
    ):
        return None

    def index_findings(
        findings: list[Any],
    ) -> dict[str, str] | None:
        indexed: dict[str, str] = {}

        for finding in findings:
            if not isinstance(finding, dict):
                return None

            finding_id = finding.get("id")
            severity = finding.get("severity")

            if (
                not isinstance(finding_id, str)
                or not finding_id
                or not isinstance(severity, str)
                or severity not in {item.label for item in Severity}
                or finding_id in indexed
            ):
                return None

            indexed[finding_id] = severity

        return indexed

    before = index_findings(previous_findings)
    after = index_findings(current_findings)

    if before is None or after is None:
        return None

    if any(
        finding_id.endswith(".execution_error")
        for finding_id in before.keys() | after.keys()
    ):
        return None

    added = tuple(
        {"id": finding_id, "severity": after[finding_id]}
        for finding_id in sorted(after.keys() - before.keys())
    )

    resolved = tuple(
        {"id": finding_id, "severity": before[finding_id]}
        for finding_id in sorted(before.keys() - after.keys())
    )

    persistent_ids = sorted(before.keys() & after.keys())

    persistent = tuple(
        {"id": finding_id, "severity": after[finding_id]}
        for finding_id in persistent_ids
    )

    severity_changed = tuple(
        {
            "id": finding_id,
            "previous_severity": before[finding_id],
            "current_severity": after[finding_id],
            "direction": (
                "worsened"
                if Severity[after[finding_id].upper()]
                > Severity[before[finding_id].upper()]
                else "improved"
            ),
        }
        for finding_id in persistent_ids
        if before[finding_id] != after[finding_id]
    )

    return FindingDeltas(
        added=added,
        resolved=resolved,
        persistent=persistent,
        severity_changed=severity_changed,
    )
