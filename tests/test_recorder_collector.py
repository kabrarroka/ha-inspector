"""Tests for the recorder collector."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.ha_inspector.engine.collectors import recorder as recorder_module
from custom_components.ha_inspector.engine.collectors.recorder import RecorderCollector
from custom_components.ha_inspector.engine.context import InspectionContext


class FakeFuture:
    def __init__(
        self,
        *,
        done: bool,
        result: bool,
    ) -> None:
        self._done = done
        self._result = result

    def done(self) -> bool:
        return self._done

    def result(self) -> bool:
        return self._result


class FakeHass:
    def __init__(self, data: dict[object, object] | None = None) -> None:
        self.data = data or {}


@pytest.mark.asyncio
async def test_collect_recorder_unavailable() -> None:
    context = InspectionContext()

    await RecorderCollector().collect(
        FakeHass(),
        context,
    )

    assert context.recorder.available is False
    assert context.recorder.reason == "Recorder instance is not available"


@pytest.mark.asyncio
async def test_collect_recorder_state(monkeypatch) -> None:
    async def async_add_executor_job(func, *args):
        return 123456789

    recorder = SimpleNamespace(
        dialect_name=SimpleNamespace(value="sqlite"),
        async_add_executor_job=async_add_executor_job,
        enabled=True,
        recording=True,
        is_running=True,
        auto_purge=True,
        auto_repack=False,
        keep_days=10,
        commit_interval=5,
        backlog=3,
        schema_version=45,
        migration_in_progress=False,
        migration_is_live=False,
        async_db_connected=FakeFuture(
            done=True,
            result=True,
        ),
        async_db_ready=FakeFuture(
            done=True,
            result=True,
        ),
    )

    monkeypatch.setattr(
        recorder_module,
        "get_instance",
        lambda hass: recorder,
    )

    hass = FakeHass(
        {
            recorder_module.DATA_INSTANCE: object(),
        }
    )

    context = InspectionContext()

    await RecorderCollector().collect(
        hass,
        context,
    )

    state = context.recorder

    assert state.available is True
    assert state.enabled is True
    assert state.recording is True
    assert state.is_running is True
    assert state.auto_purge is True
    assert state.auto_repack is False
    assert state.keep_days == 10
    assert state.commit_interval == 5
    assert state.backlog == 3
    assert state.schema_version == 45
    assert state.migration_in_progress is False
    assert state.migration_is_live is False
    assert state.database_dialect == "sqlite"
    assert state.database_connected is True
    assert state.database_ready is True
    assert state.database_size_bytes == 123456789


@pytest.mark.asyncio
async def test_collect_recorder_without_dialect(monkeypatch) -> None:
    recorder = SimpleNamespace(
        dialect_name=None,
        enabled=False,
        recording=False,
        is_running=False,
        auto_purge=False,
        auto_repack=False,
        keep_days=7,
        commit_interval=1,
        backlog=0,
        schema_version=1,
        migration_in_progress=True,
        migration_is_live=True,
        async_db_connected=FakeFuture(
            done=True,
            result=False,
        ),
        async_db_ready=FakeFuture(
            done=True,
            result=False,
        ),
    )

    monkeypatch.setattr(
        recorder_module,
        "get_instance",
        lambda hass: recorder,
    )

    hass = FakeHass(
        {
            recorder_module.DATA_INSTANCE: object(),
        }
    )

    context = InspectionContext()

    await RecorderCollector().collect(
        hass,
        context,
    )

    state = context.recorder

    assert state.database_dialect is None
    assert state.database_connected is False
    assert state.database_ready is False
    assert state.migration_in_progress is True
    assert state.migration_is_live is True


@pytest.mark.asyncio
async def test_collect_database_future_not_done(monkeypatch) -> None:
    recorder = SimpleNamespace(
        dialect_name=SimpleNamespace(value="postgresql"),
        enabled=True,
        recording=True,
        is_running=True,
        auto_purge=True,
        auto_repack=True,
        keep_days=30,
        commit_interval=2,
        backlog=1,
        schema_version=50,
        migration_in_progress=False,
        migration_is_live=False,
        async_db_connected=FakeFuture(
            done=False,
            result=True,
        ),
        async_db_ready=FakeFuture(
            done=False,
            result=True,
        ),
    )

    monkeypatch.setattr(
        recorder_module,
        "get_instance",
        lambda hass: recorder,
    )

    hass = FakeHass(
        {
            recorder_module.DATA_INSTANCE: object(),
        }
    )

    context = InspectionContext()

    await RecorderCollector().collect(
        hass,
        context,
    )

    assert context.recorder.database_dialect == "postgresql"
    assert context.recorder.database_connected is False
    assert context.recorder.database_ready is False

def test_database_size_bytes_returns_integer(monkeypatch) -> None:
    class FakeSessionContext:
        def __enter__(self):
            return object()

        def __exit__(self, exc_type, exc, tb):
            return False

    recorder = SimpleNamespace(
        dialect_name="mysql",
        db_url="mysql://user:pass@db/homeassistant",
        get_session=lambda: object(),
    )

    monkeypatch.setattr(
        recorder_module,
        "DIALECT_TO_GET_SIZE",
        {
            "mysql": lambda session, database_name: 1234.56,
        },
    )
    monkeypatch.setattr(
        recorder_module,
        "session_scope",
        lambda *, session, read_only: FakeSessionContext(),
    )

    assert recorder_module._database_size_bytes(recorder) == 1234


@pytest.mark.asyncio
async def test_collect_recorder_does_not_measure_size_when_database_not_ready(
    monkeypatch,
) -> None:
    async def async_add_executor_job(func, *args):
        raise AssertionError("executor should not be called")

    recorder = SimpleNamespace(
        dialect_name=SimpleNamespace(value="sqlite"),
        async_add_executor_job=async_add_executor_job,
        enabled=True,
        recording=True,
        is_running=True,
        auto_purge=True,
        auto_repack=False,
        keep_days=10,
        commit_interval=5,
        backlog=3,
        schema_version=45,
        migration_in_progress=False,
        migration_is_live=False,
        async_db_connected=FakeFuture(
            done=True,
            result=True,
        ),
        async_db_ready=FakeFuture(
            done=True,
            result=False,
        ),
    )

    monkeypatch.setattr(
        recorder_module,
        "get_instance",
        lambda hass: recorder,
    )

    hass = FakeHass(
        {
            recorder_module.DATA_INSTANCE: object(),
        }
    )

    context = InspectionContext()

    await RecorderCollector().collect(
        hass,
        context,
    )

    assert context.recorder.database_size_bytes is None
