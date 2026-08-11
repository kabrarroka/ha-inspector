"""Tests for the backup count inspection rule."""

from __future__ import annotations

import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.rules.backups import BackupCountRule
from custom_components.ha_inspector.engine.severity import Severity
from typing import cast
from custom_components.ha_inspector.engine.backup_state import BackupState


def _context(
    count: object,
    *,
    available: bool = True,
) -> InspectionContext:
    return InspectionContext(
        backups=BackupState(
            available=available,
            count=cast(int | None, count),
            latest="2026-08-01T09:30:00+00:00",
            oldest="2026-07-01T08:00:00+00:00",
            agent_error_count=0,
        )
    )


@pytest.mark.asyncio
async def test_three_backups_are_healthy() -> None:
    assert await BackupCountRule().check(_context(3)) == []


@pytest.mark.asyncio
async def test_more_than_three_backups_are_healthy() -> None:
    assert await BackupCountRule().check(_context(8)) == []


@pytest.mark.asyncio
@pytest.mark.parametrize("count", [1, 2])
async def test_one_or_two_backups_generate_warning(count: int) -> None:
    findings = await BackupCountRule().check(_context(count))

    assert len(findings) == 1
    assert findings[0].finding_id == "BACKUP_COUNT_LOW"
    assert findings[0].severity is Severity.WARNING
    assert findings[0].data["backup_count"] == count


@pytest.mark.asyncio
async def test_zero_backups_generates_error() -> None:
    findings = await BackupCountRule().check(_context(0))

    assert len(findings) == 1
    assert findings[0].finding_id == "BACKUP_COUNT_NONE"
    assert findings[0].severity is Severity.ERROR
    assert findings[0].data["backup_count"] == 0


@pytest.mark.asyncio
async def test_unavailable_inventory_is_ignored() -> None:
    assert await BackupCountRule().check(
        _context(None, available=False)
    ) == []


@pytest.mark.asyncio
@pytest.mark.parametrize("count", [None, "2", -1, True])
async def test_invalid_count_is_ignored(count: object) -> None:
    assert await BackupCountRule().check(_context(count)) == []
