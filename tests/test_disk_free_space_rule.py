"""Tests for the disk free-space inspection rule."""

from __future__ import annotations

from typing import cast

import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.rules.disk_free_space import (
    DiskFreeSpaceRule,
)
from custom_components.ha_inspector.engine.severity import Severity
from custom_components.ha_inspector.engine.storage_state import StorageState


def _context(free_percent: object) -> InspectionContext:
    if isinstance(free_percent, (int, float)):
        free_bytes = int(float(free_percent) * 10)
        used_bytes = 1000 - free_bytes
    else:
        free_bytes = 0
        used_bytes = 0

    return InspectionContext(
        storage=StorageState(
            total_bytes=1000,
            used_bytes=used_bytes,
            free_bytes=free_bytes,
            free_percent=cast(float, free_percent),
        )
    )


@pytest.mark.asyncio
async def test_disk_free_space_is_healthy() -> None:
    findings = await DiskFreeSpaceRule().check(_context(65.0))

    assert findings == []


@pytest.mark.asyncio
async def test_disk_free_space_warning() -> None:
    findings = await DiskFreeSpaceRule().check(_context(15.0))

    assert len(findings) == 1
    assert findings[0].finding_id == "DISK_FREE_SPACE_LOW"
    assert findings[0].severity is Severity.WARNING
    assert findings[0].data["free_percent"] == 15.0


@pytest.mark.asyncio
async def test_disk_free_space_error() -> None:
    findings = await DiskFreeSpaceRule().check(_context(5.0))

    assert len(findings) == 1
    assert findings[0].finding_id == "DISK_FREE_SPACE_CRITICAL"
    assert findings[0].severity is Severity.ERROR
    assert findings[0].data["free_percent"] == 5.0


@pytest.mark.asyncio
async def test_threshold_boundaries_are_healthy_at_twenty_percent() -> None:
    findings = await DiskFreeSpaceRule().check(_context(20.0))

    assert findings == []


@pytest.mark.asyncio
async def test_threshold_boundaries_warn_at_ten_percent() -> None:
    findings = await DiskFreeSpaceRule().check(_context(10.0))

    assert len(findings) == 1
    assert findings[0].severity is Severity.WARNING


@pytest.mark.asyncio
@pytest.mark.parametrize("free_percent", [None, "15", -1.0, 101.0])
async def test_invalid_storage_data_is_ignored(
    free_percent: object,
) -> None:
    findings = await DiskFreeSpaceRule().check(_context(free_percent))

    assert findings == []