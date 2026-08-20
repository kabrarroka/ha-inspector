"""Tests for Home Assistant Repairs issue rule."""

import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.repairs_state import RepairsState
from custom_components.ha_inspector.engine.rules.repairs import RepairIssuesRule
from custom_components.ha_inspector.engine.severity import Severity


@pytest.mark.asyncio
async def test_repairs_unavailable_returns_no_findings() -> None:
    """Unavailable Repairs registry does not produce findings."""
    context = InspectionContext()
    rule = RepairIssuesRule()

    findings = await rule.check(context)

    assert findings == []


@pytest.mark.asyncio
async def test_no_active_repairs_returns_no_findings() -> None:
    """An empty Repairs registry does not produce findings."""
    context = InspectionContext(
        repairs=RepairsState(
            available=True,
        )
    )
    rule = RepairIssuesRule()

    findings = await rule.check(context)

    assert findings == []


@pytest.mark.asyncio
async def test_repairs_are_grouped_by_severity() -> None:
    """Active issues produce one finding per severity."""
    context = InspectionContext(
        repairs=RepairsState(
            available=True,
            total=3,
            critical=1,
            error=1,
            warning=1,
            fixable=2,
            issues=[
                {
                    "domain": "demo",
                    "issue_id": "critical",
                    "severity": "critical",
                    "is_fixable": True,
                    "breaks_in_ha_version": "2026.9.0",
                },
                {
                    "domain": "demo",
                    "issue_id": "error",
                    "severity": "error",
                    "is_fixable": True,
                    "breaks_in_ha_version": None,
                },
                {
                    "domain": "demo",
                    "issue_id": "warning",
                    "severity": "warning",
                    "is_fixable": False,
                    "breaks_in_ha_version": None,
                },
            ],
        )
    )
    rule = RepairIssuesRule()

    findings = await rule.check(context)

    assert [finding.finding_id for finding in findings] == [
        "REPAIR_ISSUES_CRITICAL",
        "REPAIR_ISSUES_ERROR",
        "REPAIR_ISSUES_WARNING",
    ]

    assert [finding.severity for finding in findings] == [
        Severity.CRITICAL,
        Severity.ERROR,
        Severity.WARNING,
    ]

    assert findings[0].data["count"] == 1
    assert findings[0].data["total"] == 3
    assert findings[0].data["fixable"] == 2


@pytest.mark.asyncio
async def test_only_present_severity_is_reported() -> None:
    """Only severity groups with active issues produce findings."""
    context = InspectionContext(
        repairs=RepairsState(
            available=True,
            total=1,
            warning=1,
            issues=[
                {
                    "domain": "demo",
                    "issue_id": "warning",
                    "severity": "warning",
                    "is_fixable": False,
                    "breaks_in_ha_version": None,
                }
            ],
        )
    )
    rule = RepairIssuesRule()

    findings = await rule.check(context)

    assert len(findings) == 1
    assert findings[0].finding_id == "REPAIR_ISSUES_WARNING"
    assert findings[0].severity is Severity.WARNING
