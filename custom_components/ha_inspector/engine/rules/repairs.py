"""Home Assistant Repairs issue rules."""

from __future__ import annotations

from ..context import InspectionContext
from ..models import Finding
from ..severity import Severity
from .base import BaseRule


class RepairIssuesRule(BaseRule):
    """Inspect active Home Assistant Repairs issues."""

    rule_id = "REPAIR_ISSUES"

    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        """Check active Repairs issues."""
        repairs = context.repairs

        if not repairs.available or not repairs.issues:
            return []

        findings: list[Finding] = []

        severity_config = (
            (
                "critical",
                Severity.CRITICAL,
                "REPAIR_ISSUES_CRITICAL",
                "Critical Home Assistant repair issues are active",
            ),
            (
                "error",
                Severity.ERROR,
                "REPAIR_ISSUES_ERROR",
                "Home Assistant repair errors are active",
            ),
            (
                "warning",
                Severity.WARNING,
                "REPAIR_ISSUES_WARNING",
                "Home Assistant repair warnings are active",
            ),
        )

        for (
            issue_severity,
            finding_severity,
            finding_id,
            title,
        ) in severity_config:
            issues = [
                issue
                for issue in repairs.issues
                if issue.get("severity") == issue_severity
            ]

            if not issues:
                continue

            count = len(issues)
            fixable_count = sum(
                bool(issue.get("is_fixable"))
                for issue in issues
            )
            breaking_count = sum(
                bool(issue.get("breaks_in_ha_version"))
                for issue in issues
            )

            recommendation_parts = [
                "Open Settings > System > Repairs in Home Assistant "
                "and review the affected issues."
            ]

            if fixable_count:
                recommendation_parts.append(
                    f"{fixable_count} issue(s) in this group are fixable "
                    "directly from Repairs."
                )

            if breaking_count:
                recommendation_parts.append(
                    f"{breaking_count} issue(s) can break in a future "
                    "Home Assistant version; review them before upgrading."
                )

            if not fixable_count and not breaking_count:
                recommendation_parts.append(
                    "Follow the guidance provided by Home Assistant for "
                    "each issue."
                )

            findings.append(
                Finding(
                    finding_id=finding_id,
                    severity=finding_severity,
                    title=title,
                    description=(
                        f"{count} active Home Assistant Repairs issue(s) "
                        f"have {issue_severity} severity."
                    ),
                    recommendation=" ".join(recommendation_parts),
                    data={
                        "count": count,
                        "total": repairs.total,
                        "fixable": repairs.fixable,
                        "fixable_count": fixable_count,
                        "breaking": repairs.breaking,
                        "breaking_count": breaking_count,
                        "learn_more": repairs.learn_more,
                        "issues": issues,
                    },
                )
            )

        return findings
