"""Tests for the backup integrity inspection rule."""

from __future__ import annotations

import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.rules.backups import BackupIntegrityRule
from custom_components.ha_inspector.engine.severity import Severity
from typing import cast
from custom_components.ha_inspector.engine.backup_state import BackupState


def _context(
    *,
    failed_addons: object = None,
    failed_folders: object = None,
    failed_agent_ids: object = None,
    available: bool = True,
    count: object = 3,
) -> InspectionContext:
    return InspectionContext(
        backups=BackupState(
            available=available,
            count=cast(int | None, count),
            latest="2026-08-05T06:00:00+00:00",
            latest_backup_failed_addons=cast(
                list[str],
                [] if failed_addons is None else failed_addons,
            ),
            latest_backup_failed_folders=cast(
                list[str],
                [] if failed_folders is None else failed_folders,
            ),
            latest_backup_failed_agent_ids=cast(
                list[str],
                [] if failed_agent_ids is None else failed_agent_ids,
            ),
        )
    )


@pytest.mark.asyncio
async def test_complete_latest_backup_is_healthy() -> None:
    assert await BackupIntegrityRule().check(_context()) == []


@pytest.mark.asyncio
async def test_failed_addon_generates_error() -> None:
    findings = await BackupIntegrityRule().check(
        _context(failed_addons=["mosquitto"])
    )

    assert len(findings) == 1
    assert findings[0].finding_id == "BACKUP_INTEGRITY_INCOMPLETE"
    assert findings[0].severity is Severity.ERROR
    assert findings[0].data["failed_addons"] == ["mosquitto"]
    assert findings[0].data["content_incomplete"] is True


@pytest.mark.asyncio
async def test_failed_folder_generates_error() -> None:
    findings = await BackupIntegrityRule().check(
        _context(failed_folders=["media"])
    )

    assert findings[0].severity is Severity.ERROR
    assert findings[0].data["failed_folders"] == ["media"]


@pytest.mark.asyncio
async def test_only_failed_agents_generates_warning() -> None:
    findings = await BackupIntegrityRule().check(
        _context(failed_agent_ids=["cloud"])
    )

    assert findings[0].finding_id == "BACKUP_INTEGRITY_AGENT_FAILURES"
    assert findings[0].severity is Severity.WARNING
    assert findings[0].data["storage_incomplete"] is True


@pytest.mark.asyncio
async def test_content_failure_takes_precedence_over_agent_failure() -> None:
    findings = await BackupIntegrityRule().check(
        _context(
            failed_addons=["addon"],
            failed_agent_ids=["cloud"],
        )
    )

    assert findings[0].severity is Severity.ERROR
    assert findings[0].data["failed_agent_ids"] == ["cloud"]


@pytest.mark.asyncio
async def test_values_are_normalized() -> None:
    findings = await BackupIntegrityRule().check(
        _context(
            failed_addons=[" addon ", "addon", "", 123],
            failed_folders=[" media ", "media", ""],
            failed_agent_ids=[" cloud ", "cloud", ""],
        )
    )

    assert findings[0].data["failed_addons"] == ["addon"]
    assert findings[0].data["failed_folders"] == ["media"]
    assert findings[0].data["failed_agent_ids"] == ["cloud"]


@pytest.mark.asyncio
async def test_unavailable_inventory_is_ignored() -> None:
    assert await BackupIntegrityRule().check(
        _context(failed_addons=["addon"], available=False)
    ) == []


@pytest.mark.asyncio
@pytest.mark.parametrize("count", [None, "1", 0, -1, True])
async def test_missing_or_invalid_backup_count_is_ignored(count: object) -> None:
    assert await BackupIntegrityRule().check(
        _context(failed_addons=["addon"], count=count)
    ) == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("failed_addons", "addon"),
        ("failed_folders", {}),
        ("failed_agent_ids", ()),
    ],
)
async def test_invalid_failure_collections_are_ignored(
    field: str,
    value: object,
) -> None:
    kwargs = {field: value}
    assert await BackupIntegrityRule().check(_context(**kwargs)) == []
