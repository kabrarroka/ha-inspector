"""Tests for the backup redundancy inspection rule."""

from __future__ import annotations

from typing import cast

import pytest

from custom_components.ha_inspector.engine.backup_state import BackupState
from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.rules.backups import BackupRedundancyRule
from custom_components.ha_inspector.engine.severity import Severity

_DEFAULT_AGENT_IDS = object()


def _context(
    *,
    count: object = 3,
    agent_count: object = 2,
    agent_ids: object = _DEFAULT_AGENT_IDS,
    available: bool = True,
) -> InspectionContext:
    resolved_agent_ids: object

    if agent_ids is _DEFAULT_AGENT_IDS:
        resolved_agent_ids = ["local", "cloud"]
    else:
        resolved_agent_ids = agent_ids

    return InspectionContext(
        backups=BackupState(
            available=available,
            count=cast(int | None, count),
            latest="2026-08-05T06:00:00+00:00",
            latest_backup_agent_count=cast(int, agent_count),
            latest_backup_agent_ids=cast(
                list[str],
                resolved_agent_ids,
            ),
        )
    )


@pytest.mark.asyncio
async def test_two_backup_agents_are_healthy() -> None:
    assert await BackupRedundancyRule().check(_context()) == []


@pytest.mark.asyncio
async def test_more_than_two_backup_agents_are_healthy() -> None:
    assert await BackupRedundancyRule().check(
        _context(
            agent_count=3,
            agent_ids=["local", "cloud", "nas"],
        )
    ) == []


@pytest.mark.asyncio
async def test_one_backup_agent_generates_warning() -> None:
    findings = await BackupRedundancyRule().check(
        _context(
            agent_count=1,
            agent_ids=["local"],
        )
    )

    assert len(findings) == 1

    finding = findings[0]

    assert finding.finding_id == "BACKUP_REDUNDANCY_LOW"
    assert finding.severity is Severity.WARNING
    assert finding.data == {
        "latest_backup": "2026-08-05T06:00:00+00:00",
        "latest_backup_agent_count": 1,
        "latest_backup_agent_ids": ["local"],
        "minimum_recommended_agents": 2,
    }


@pytest.mark.asyncio
async def test_zero_backup_agents_generates_warning() -> None:
    findings = await BackupRedundancyRule().check(
        _context(
            agent_count=0,
            agent_ids=[],
        )
    )

    assert len(findings) == 1
    assert findings[0].finding_id == "BACKUP_REDUNDANCY_LOW"
    assert findings[0].severity is Severity.WARNING
    assert findings[0].data["latest_backup_agent_count"] == 0


@pytest.mark.asyncio
async def test_agent_ids_are_normalized() -> None:
    findings = await BackupRedundancyRule().check(
        _context(
            agent_count=1,
            agent_ids=[
                " cloud ",
                "cloud",
                "",
                "   ",
                123,
            ],
        )
    )

    assert findings[0].data["latest_backup_agent_ids"] == ["cloud"]


@pytest.mark.asyncio
async def test_unavailable_inventory_is_ignored() -> None:
    assert await BackupRedundancyRule().check(
        _context(
            available=False,
            agent_count=1,
            agent_ids=["local"],
        )
    ) == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "count",
    [
        None,
        "1",
        0,
        -1,
        True,
    ],
)
async def test_missing_or_invalid_backup_count_is_ignored(
    count: object,
) -> None:
    assert await BackupRedundancyRule().check(
        _context(
            count=count,
            agent_count=1,
            agent_ids=["local"],
        )
    ) == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "agent_count",
    [
        None,
        "1",
        -1,
        True,
    ],
)
async def test_invalid_agent_count_is_ignored(
    agent_count: object,
) -> None:
    assert await BackupRedundancyRule().check(
        _context(
            agent_count=agent_count,
            agent_ids=["local"],
        )
    ) == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "agent_ids",
    [
        None,
        "local",
        {},
        (),
    ],
)
async def test_invalid_agent_ids_are_ignored(
    agent_ids: object,
) -> None:
    assert await BackupRedundancyRule().check(
        _context(
            agent_count=1,
            agent_ids=agent_ids,
        )
    ) == []