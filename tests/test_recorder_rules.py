import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.recorder_state import RecorderState
from custom_components.ha_inspector.engine.rules.recorder import (
    RecorderAvailabilityRule,
    RecorderDatabaseSizeRule,
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


@pytest.mark.asyncio
async def test_recorder_database_size_returns_nothing_when_unavailable() -> None:
    context = InspectionContext(
        recorder=RecorderState(
            available=False,
            database_size_bytes=20 * 1024**3,
        )
    )

    assert await RecorderDatabaseSizeRule().check(context) == []


@pytest.mark.asyncio
async def test_recorder_database_size_returns_nothing_when_unknown() -> None:
    context = InspectionContext(
        recorder=RecorderState(
            available=True,
            database_size_bytes=None,
        )
    )

    assert await RecorderDatabaseSizeRule().check(context) == []


@pytest.mark.asyncio
async def test_recorder_database_size_reports_warning() -> None:
    size_bytes = 6 * 1024**3

    context = InspectionContext(
        recorder=RecorderState(
            available=True,
            database_size_bytes=size_bytes,
        )
    )

    findings = await RecorderDatabaseSizeRule().check(context)

    assert len(findings) == 1
    finding = findings[0]

    assert finding.finding_id == "RECORDER_DATABASE_SIZE_HIGH"
    assert finding.severity is Severity.WARNING
    assert finding.data == {
        "database_size_bytes": size_bytes,
        "warning_threshold_bytes": 5 * 1024**3,
    }


@pytest.mark.asyncio
async def test_recorder_database_size_reports_error() -> None:
    size_bytes = 11 * 1024**3

    context = InspectionContext(
        recorder=RecorderState(
            available=True,
            database_size_bytes=size_bytes,
        )
    )

    findings = await RecorderDatabaseSizeRule().check(context)

    assert len(findings) == 1
    finding = findings[0]

    assert finding.finding_id == "RECORDER_DATABASE_SIZE_EXCESSIVE"
    assert finding.severity is Severity.ERROR
    assert finding.data == {
        "database_size_bytes": size_bytes,
        "warning_threshold_bytes": 5 * 1024**3,
        "error_threshold_bytes": 10 * 1024**3,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "size_bytes",
    [
        0,
        5 * 1024**3,
    ],
)
async def test_recorder_database_size_returns_nothing_at_thresholds(
    size_bytes: int,
) -> None:
    context = InspectionContext(
        recorder=RecorderState(
            available=True,
            database_size_bytes=size_bytes,
        )
    )

    assert await RecorderDatabaseSizeRule().check(context) == []


def test_recorder_keep_days_default_thresholds() -> None:
    """Recorder retention uses backward-compatible default thresholds."""
    rule = RecorderKeepDaysRule()

    assert rule.warning_threshold == 30
    assert rule.error_threshold == 90


@pytest.mark.asyncio
async def test_recorder_keep_days_custom_thresholds() -> None:
    """Configured retention thresholds control finding severity."""
    context = InspectionContext(
        recorder=RecorderState(
            available=True,
            keep_days=46,
        )
    )

    rule = RecorderKeepDaysRule(
        warning_threshold=45,
        error_threshold=60,
    )

    findings = await rule.check(context)

    assert len(findings) == 1
    assert findings[0].finding_id == "RECORDER_KEEP_DAYS_HIGH"
    assert findings[0].severity is Severity.WARNING
    assert findings[0].data == {
        "keep_days": 46,
        "warning_threshold": 45,
    }


def test_recorder_keep_days_accepts_boundary_thresholds() -> None:
    """Zero and equal retention thresholds are valid."""
    rule = RecorderKeepDaysRule(
        warning_threshold=0,
        error_threshold=0,
    )

    assert rule.warning_threshold == 0
    assert rule.error_threshold == 0


@pytest.mark.parametrize(
    ("warning_threshold", "error_threshold"),
    [
        (-1, 90),
        (30, -1),
        (91, 90),
    ],
)
def test_recorder_keep_days_rejects_invalid_thresholds(
    warning_threshold: int,
    error_threshold: int,
) -> None:
    """Invalid retention threshold ordering is rejected."""
    with pytest.raises(
        ValueError,
        match="Recorder keep-days thresholds",
    ):
        RecorderKeepDaysRule(
            warning_threshold=warning_threshold,
            error_threshold=error_threshold,
        )


def test_recorder_database_size_default_thresholds() -> None:
    """Recorder database size uses backward-compatible defaults."""
    rule = RecorderDatabaseSizeRule()

    assert rule.warning_threshold_bytes == 5 * 1024**3
    assert rule.error_threshold_bytes == 10 * 1024**3


@pytest.mark.asyncio
async def test_recorder_database_size_custom_thresholds() -> None:
    """Configured database-size thresholds control finding severity."""
    size_bytes = 3 * 1024**3

    context = InspectionContext(
        recorder=RecorderState(
            available=True,
            database_size_bytes=size_bytes,
        )
    )

    rule = RecorderDatabaseSizeRule(
        warning_threshold_bytes=2 * 1024**3,
        error_threshold_bytes=4 * 1024**3,
    )

    findings = await rule.check(context)

    assert len(findings) == 1
    assert findings[0].finding_id == "RECORDER_DATABASE_SIZE_HIGH"
    assert findings[0].severity is Severity.WARNING
    assert findings[0].data == {
        "database_size_bytes": size_bytes,
        "warning_threshold_bytes": 2 * 1024**3,
    }


def test_recorder_database_size_accepts_boundary_thresholds() -> None:
    """Zero and equal database-size thresholds are valid."""
    rule = RecorderDatabaseSizeRule(
        warning_threshold_bytes=0,
        error_threshold_bytes=0,
    )

    assert rule.warning_threshold_bytes == 0
    assert rule.error_threshold_bytes == 0


@pytest.mark.parametrize(
    ("warning_threshold_bytes", "error_threshold_bytes"),
    [
        (-1, 10 * 1024**3),
        (5 * 1024**3, -1),
        (11 * 1024**3, 10 * 1024**3),
    ],
)
def test_recorder_database_size_rejects_invalid_thresholds(
    warning_threshold_bytes: int,
    error_threshold_bytes: int,
) -> None:
    """Invalid database-size threshold ordering is rejected."""
    with pytest.raises(
        ValueError,
        match="Recorder database-size thresholds",
    ):
        RecorderDatabaseSizeRule(
            warning_threshold_bytes=warning_threshold_bytes,
            error_threshold_bytes=error_threshold_bytes,
        )
