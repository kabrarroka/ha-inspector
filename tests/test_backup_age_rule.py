"""Tests for the backup age inspection rule."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast

import pytest

from custom_components.ha_inspector.engine.backup_state import BackupState
from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.rules.backup_age import BackupAgeRule
from custom_components.ha_inspector.engine.severity import Severity


class FixedTimeBackupAgeRule(BackupAgeRule):
    """Backup age rule with a fixed current time for testing."""

    def _now(self) -> datetime:
        return datetime(2026, 8, 4, 8, 0, tzinfo=UTC)


def _context(
    latest: object,
    *,
    available: bool = True,
    count: object = 3,
) -> InspectionContext:
    return InspectionContext(
        backups=BackupState(
            available=available,
            count=cast(int | None, count),
            latest=cast(str | None, latest),
            oldest=None,
        )
    )


@pytest.mark.asyncio
async def test_recent_backup_is_healthy() -> None:
    findings = await FixedTimeBackupAgeRule().check(
        _context("2026-08-02T08:00:00+00:00")
    )

    assert findings == []


@pytest.mark.asyncio
async def test_seven_day_old_backup_generates_warning() -> None:
    findings = await FixedTimeBackupAgeRule().check(
        _context("2026-07-28T08:00:00+00:00")
    )

    assert len(findings) == 1
    assert findings[0].finding_id == "BACKUP_AGE_HIGH"
    assert findings[0].severity is Severity.WARNING
    assert findings[0].data["backup_age_days"] == 7


@pytest.mark.asyncio
async def test_twenty_nine_day_old_backup_generates_warning() -> None:
    findings = await FixedTimeBackupAgeRule().check(
        _context("2026-07-06T08:00:00+00:00")
    )

    assert len(findings) == 1
    assert findings[0].severity is Severity.WARNING
    assert findings[0].data["backup_age_days"] == 29


@pytest.mark.asyncio
async def test_thirty_day_old_backup_generates_error() -> None:
    findings = await FixedTimeBackupAgeRule().check(
        _context("2026-07-05T08:00:00+00:00")
    )

    assert len(findings) == 1
    assert findings[0].finding_id == "BACKUP_AGE_CRITICAL"
    assert findings[0].severity is Severity.ERROR
    assert findings[0].data["backup_age_days"] == 30


@pytest.mark.asyncio
async def test_old_backup_includes_backup_count() -> None:
    findings = await FixedTimeBackupAgeRule().check(
        _context(
            "2026-07-01T08:00:00+00:00",
            count=5,
        )
    )

    assert findings[0].data["backup_count"] == 5


@pytest.mark.asyncio
async def test_unavailable_backup_inventory_is_ignored() -> None:
    findings = await FixedTimeBackupAgeRule().check(
        _context(
            "2026-07-01T08:00:00+00:00",
            available=False,
        )
    )

    assert findings == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "latest",
    [
        None,
        "",
        "invalid-date",
        "2026-07-01T08:00:00",
        123,
    ],
)
async def test_invalid_latest_backup_date_is_ignored(
    latest: object,
) -> None:
    findings = await FixedTimeBackupAgeRule().check(_context(latest))

    assert findings == []


@pytest.mark.asyncio
async def test_future_backup_date_is_ignored() -> None:
    findings = await FixedTimeBackupAgeRule().check(
        _context("2026-08-05T08:00:00+00:00")
    )

    assert findings == []


@pytest.mark.asyncio
async def test_backup_date_timezone_is_normalized_to_utc() -> None:
    findings = await FixedTimeBackupAgeRule().check(
        _context("2026-07-05T10:00:00+02:00")
    )

    assert len(findings) == 1
    assert findings[0].data["backup_age_days"] == 30
    assert findings[0].data["latest_backup"] == (
        "2026-07-05T08:00:00+00:00"
    )

def test_now_returns_timezone_aware_utc_datetime() -> None:
    now = BackupAgeRule()._now()

    assert now.tzinfo is UTC