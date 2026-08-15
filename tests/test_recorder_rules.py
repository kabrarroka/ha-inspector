import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.recorder_state import RecorderState
from custom_components.ha_inspector.engine.rules.recorder import (
    RecorderAvailabilityRule,
    RecorderKeepDaysRule,
)
from custom_components.ha_inspector.engine.severity import Severity


@pytest.mark.asyncio
async def test_recorder_availability_reports_unavailable() -> None:
    context = InspectionContext(
        recorder=RecorderState(
            available=False,
        )
    )

    findings = await RecorderAvailabilityRule().check(context)

    assert len(findings) == 1

    finding = findings[0]

    assert finding.finding_id == "RECORDER_UNAVAILABLE"
    assert finding.severity is Severity.ERROR


@pytest.mark.asyncio
async def test_recorder_availability_reports_database_not_connected() -> None:
    context = InspectionContext(
        recorder=RecorderState(
            available=True,
            database_connected=False,
            database_dialect="sqlite",
        )
    )

    findings = await RecorderAvailabilityRule().check(context)

    assert len(findings) == 1

    finding = findings[0]

    assert finding.finding_id == "RECORDER_DATABASE_NOT_CONNECTED"
    assert finding.severity is Severity.ERROR
    assert finding.data == {
        "database_dialect": "sqlite",
    }


@pytest.mark.asyncio
async def test_recorder_availability_reports_database_not_ready() -> None:
    context = InspectionContext(
        recorder=RecorderState(
            available=True,
            database_connected=True,
            database_ready=False,
            migration_in_progress=True,
        )
    )

    findings = await RecorderAvailabilityRule().check(context)

    assert len(findings) == 1

    finding = findings[0]

    assert finding.finding_id == "RECORDER_DATABASE_NOT_READY"
    assert finding.severity is Severity.WARNING
    assert finding.data == {
        "migration_in_progress": True,
    }


@pytest.mark.asyncio
async def test_recorder_availability_returns_nothing_when_healthy() -> None:
    context = InspectionContext(
        recorder=RecorderState(
            available=True,
            database_connected=True,
            database_ready=True,
        )
    )

    assert await RecorderAvailabilityRule().check(context) == []


@pytest.mark.asyncio
async def test_recorder_keep_days_returns_nothing_when_unavailable() -> None:
    context = InspectionContext(
        recorder=RecorderState(
            available=False,
            keep_days=100,
        )
    )

    assert await RecorderKeepDaysRule().check(context) == []


@pytest.mark.asyncio
async def test_recorder_keep_days_reports_unknown_value() -> None:
    context = InspectionContext(
        recorder=RecorderState(
            available=True,
            keep_days=None,
        )
    )

    findings = await RecorderKeepDaysRule().check(context)

    assert len(findings) == 1

    finding = findings[0]

    assert finding.finding_id == "RECORDER_KEEP_DAYS_UNKNOWN"
    assert finding.severity is Severity.WARNING


@pytest.mark.asyncio
async def test_recorder_keep_days_reports_excessive_retention() -> None:
    context = InspectionContext(
        recorder=RecorderState(
            available=True,
            keep_days=91,
        )
    )

    findings = await RecorderKeepDaysRule().check(context)

    assert len(findings) == 1

    finding = findings[0]

    assert finding.finding_id == "RECORDER_KEEP_DAYS_EXCESSIVE"
    assert finding.severity is Severity.ERROR
    assert finding.data == {
        "keep_days": 91,
        "warning_threshold": 30,
        "error_threshold": 90,
    }


@pytest.mark.asyncio
async def test_recorder_keep_days_reports_high_retention() -> None:
    context = InspectionContext(
        recorder=RecorderState(
            available=True,
            keep_days=31,
        )
    )

    findings = await RecorderKeepDaysRule().check(context)

    assert len(findings) == 1

    finding = findings[0]

    assert finding.finding_id == "RECORDER_KEEP_DAYS_HIGH"
    assert finding.severity is Severity.WARNING
    assert finding.data == {
        "keep_days": 31,
        "warning_threshold": 30,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "keep_days",
    [
        0,
        30,
    ],
)
async def test_recorder_keep_days_returns_nothing_with_acceptable_retention(
    keep_days: int,
) -> None:
    context = InspectionContext(
        recorder=RecorderState(
            available=True,
            keep_days=keep_days,
        )
    )

    assert await RecorderKeepDaysRule().check(context) == []