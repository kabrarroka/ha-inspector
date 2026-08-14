"""Tests for the storage collector."""

from __future__ import annotations

from collections import namedtuple

import pytest

from custom_components.ha_inspector.engine.collectors import storage as storage_module
from custom_components.ha_inspector.engine.collectors.storage import StorageCollector
from custom_components.ha_inspector.engine.context import InspectionContext

DiskUsage = namedtuple("DiskUsage", "total used free")


class FakeConfig:
    def path(self) -> str:
        return "/config"


class FakeHass:
    def __init__(self) -> None:
        self.config = FakeConfig()

    async def async_add_executor_job(self, func, *args):
        return func(*args)


@pytest.mark.asyncio
async def test_collect_storage_statistics(monkeypatch) -> None:
    monkeypatch.setattr(
        storage_module.shutil,
        "disk_usage",
        lambda path: DiskUsage(
            total=1_000,
            used=400,
            free=600,
        ),
    )

    context = InspectionContext()

    await StorageCollector().collect(
        FakeHass(),
        context,
    )

    assert context.storage.total_bytes == 1_000
    assert context.storage.used_bytes == 400
    assert context.storage.free_bytes == 600
    assert context.storage.free_percent == 60.0


@pytest.mark.asyncio
async def test_collect_storage_rounds_free_percent(monkeypatch) -> None:
    monkeypatch.setattr(
        storage_module.shutil,
        "disk_usage",
        lambda path: DiskUsage(
            total=3,
            used=2,
            free=1,
        ),
    )

    context = InspectionContext()

    await StorageCollector().collect(
        FakeHass(),
        context,
    )

    assert context.storage.free_percent == 33.33


@pytest.mark.asyncio
async def test_collect_storage_with_zero_total(monkeypatch) -> None:
    monkeypatch.setattr(
        storage_module.shutil,
        "disk_usage",
        lambda path: DiskUsage(
            total=0,
            used=0,
            free=0,
        ),
    )

    context = InspectionContext()

    await StorageCollector().collect(
        FakeHass(),
        context,
    )

    assert context.storage.total_bytes == 0
    assert context.storage.used_bytes == 0
    assert context.storage.free_bytes == 0
    assert context.storage.free_percent == 0.0