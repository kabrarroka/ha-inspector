"""Tests for system log health rules."""

import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.logs_state import LogsState
from custom_components.ha_inspector.engine.rules.logs import LogHealthRule
from custom_components.ha_inspector.engine.severity import Severity


@pytest.mark.asyncio
async def test_log_rule_returns_nothing_when_unavailable() -> None:
    context = InspectionContext(
        logs=LogsState(available=False)
    )

    assert await LogHealthRule().check(context) == []


@pytest.mark.asyncio
async def test_log_rule_returns_nothing_when_clean() -> None:
    context = InspectionContext(
        logs=LogsState(available=True)
    )

    assert await LogHealthRule().check(context) == []


@pytest.mark.asyncio
async def test_log_rule_reports_errors() -> None:
    context = InspectionContext(
        logs=LogsState(
            available=True,
            error_entries=2,
            error_occurrences=7,
        )
    )

    findings = await LogHealthRule().check(context)

    assert len(findings) == 1
    assert findings[0].finding_id == "SYSTEM_LOG_ERRORS"
    assert findings[0].severity is Severity.ERROR


@pytest.mark.asyncio
async def test_log_rule_reports_warnings() -> None:
    context = InspectionContext(
        logs=LogsState(
            available=True,
            warning_entries=3,
            warning_occurrences=5,
        )
    )

    findings = await LogHealthRule().check(context)

    assert len(findings) == 1
    assert findings[0].finding_id == "SYSTEM_LOG_WARNINGS"
    assert findings[0].severity is Severity.WARNING


@pytest.mark.asyncio
async def test_log_rule_can_report_errors_and_warnings() -> None:
    context = InspectionContext(
        logs=LogsState(
            available=True,
            warning_entries=1,
            error_entries=1,
            warning_occurrences=2,
            error_occurrences=3,
        )
    )

    findings = await LogHealthRule().check(context)

    assert {
        finding.finding_id
        for finding in findings
    } == {
        "SYSTEM_LOG_ERRORS",
        "SYSTEM_LOG_WARNINGS",
    }
