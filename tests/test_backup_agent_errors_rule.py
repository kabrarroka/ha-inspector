"""Tests for the backup agent errors inspection rule."""

from __future__ import annotations

from typing import cast

import pytest

from custom_components.ha_inspector.engine.backup_state import BackupState
from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.rules.backups import (
    BackupAgentErrorsRule,
)
from custom_components.ha_inspector.engine.severity import Severity


def _context(
    error_count: object,
    error_ids: object,
    *,
    available: bool = True,
) -> InspectionContext:
    return InspectionContext(
        backups=BackupState(
            available=available,
            count=4,
            latest="2026-08-01T09:30:00+00:00",
            oldest="2026-07-01T08:00:00+00:00",
            agent_error_count=cast(int, error_count),
            agent_error_ids=cast(list[str], error_ids),
        )
    )


@pytest.mark.asyncio
async def test_no_agent_errors_is_healthy() -> None:
    findings = await BackupAgentErrorsRule().check(
        _context(0, [])
    )

    assert findings == []


@pytest.mark.asyncio
async def test_one_agent_error_generates_warning() -> None:
    findings = await BackupAgentErrorsRule().check(
        _context(1, ["cloud"])
    )

    assert len(findings) == 1
    assert findings[0].finding_id == "BACKUP_AGENT_ERRORS_FOUND"
    assert findings[0].severity is Severity.WARNING
    assert findings[0].data["agent_error_count"] == 1
    assert findings[0].data["agent_error_ids"] == ["cloud"]


@pytest.mark.asyncio
async def test_multiple_agent_errors_generate_single_warning() -> None:
    findings = await BackupAgentErrorsRule().check(
        _context(
            3,
            [
                "nas",
                "cloud",
                "remote",
            ],
        )
    )

    assert len(findings) == 1
    assert findings[0].severity is Severity.WARNING
    assert findings[0].data["agent_error_count"] == 3
    assert findings[0].data["backup_count"] == 4
    assert findings[0].data["latest_backup"] == (
        "2026-08-01T09:30:00+00:00"
    )


@pytest.mark.asyncio
async def test_agent_ids_are_normalized() -> None:
    findings = await BackupAgentErrorsRule().check(
        _context(
            3,
            [
                " nas ",
                "cloud",
                "nas",
                "",
                "   ",
                123,
            ],
        )
    )

    assert findings[0].data["agent_error_ids"] == [
        "cloud",
        "nas",
    ]


@pytest.mark.asyncio
async def test_unavailable_inventory_is_ignored() -> None:
    findings = await BackupAgentErrorsRule().check(
        _context(
            1,
            ["cloud"],
            available=False,
        )
    )

    assert findings == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error_count",
    [
        None,
        "1",
        -1,
        0,
        True,
    ],
)
async def test_invalid_error_count_is_ignored(
    error_count: object,
) -> None:
    findings = await BackupAgentErrorsRule().check(
        _context(error_count, ["cloud"])
    )

    assert findings == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error_ids",
    [
        None,
        "cloud",
        {},
        (),
    ],
)
async def test_invalid_agent_error_ids_are_ignored(
    error_ids: object,
) -> None:
    findings = await BackupAgentErrorsRule().check(
        _context(1, error_ids)
    )

    assert findings == []