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

            findings.append(
                Finding(
                    finding_id=finding_id,
                    severity=finding_severity,
                    title=title,
                    description=(
                        f"{count} active Home Assistant Repairs issue(s) "
                        f"have {issue_severity} severity."
                    ),
                    recommendation=(
                        "Open Settings > System > Repairs in Home Assistant "
                        "and review the affected issues. Resolve fixable "
                        "issues and follow the provided guidance before "
                        "upgrading if an issue can break in a future version."
                    ),
                    data={
                        "count": count,
                        "total": repairs.total,
                        "fixable": repairs.fixable,
                        "issues": issues,
                    },
                )
            )

        return findings
