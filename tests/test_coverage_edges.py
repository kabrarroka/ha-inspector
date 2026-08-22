"""Coverage tests for defensive collector and persistence branches."""

from __future__ import annotations

import builtins
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.backup.const import DATA_MANAGER

from custom_components.ha_inspector.engine.collectors import addons as addons_module
from custom_components.ha_inspector.engine.collectors import recorder as recorder_module
from custom_components.ha_inspector.engine.collectors import repairs as repairs_module
from custom_components.ha_inspector.engine.collectors import system as system_module
from custom_components.ha_inspector.engine.collectors.backups import BackupCollector
from custom_components.ha_inspector.engine.collectors.logs import _collect_logs_state
from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.restart_history import RestartHistory


def _block_import(
    monkeypatch: pytest.MonkeyPatch,
    *,
    module: str,
    from_name: str | None = None,
) -> None:
    """Make one runtime import fail while leaving all other imports intact."""
    real_import = builtins.__import__

    def fake_import(
        name: str,
        globals=None,
        locals=None,
        fromlist=(),
        level: int = 0,
    ):
        if name == module and (
            from_name is None or from_name in fromlist
        ):
            raise ImportError(f"blocked test import: {module}")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)


def test_addons_unavailable_without_hassio(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing Supervisor modules produce an unavailable add-on state."""
    _block_import(
        monkeypatch,
        module="homeassistant.components.hassio.coordinator",
    )

    state = addons_module._collect_addons_state(SimpleNamespace())

    assert state.available is False


def test_addons_unavailable_when_supervisor_not_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Supervisor-not-ready is handled without failing inspection."""
    class FakeNotReadyError(Exception):
        pass

    monkeypatch.setitem(
        __import__("sys").modules,
        "homeassistant.components.hassio.coordinator",
        SimpleNamespace(
            get_addons_list=lambda hass: (_ for _ in ()).throw(
                FakeNotReadyError()
            )
        ),
    )
    monkeypatch.setitem(
        __import__("sys").modules,
        "homeassistant.components.hassio.exceptions",
        SimpleNamespace(HassioNotReadyError=FakeNotReadyError),
    )

    state = addons_module._collect_addons_state(SimpleNamespace())

    assert state.available is False


@pytest.mark.asyncio
async def test_addons_collector_updates_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The public collector stores its result in the inspection context."""
    monkeypatch.setattr(
        addons_module,
        "_collect_addons_state",
        lambda hass: addons_module.AddonsState(available=True),
    )
    context = InspectionContext()

    await addons_module.AddonsCollector().collect(
        SimpleNamespace(),
        context,
    )

    assert context.addons.available is True


@pytest.mark.asyncio
async def test_backup_collector_accepts_datetime_and_ignores_bad_dates() -> None:
    """Backup dates accept datetime values and reject malformed values."""
    valid_date = datetime(2026, 8, 20, 8, 30, tzinfo=UTC)
    manager = MagicMock()
    manager.async_get_backups = AsyncMock(
        return_value=(
            {
                "valid": SimpleNamespace(
                    date=valid_date,
                    agents={},
                    failed_addons=[],
                    failed_folders=[],
                    failed_agent_ids=[],
                ),
                "invalid-string": SimpleNamespace(date="not-a-date"),
                "invalid-type": SimpleNamespace(date=123),
            },
            {},
        )
    )
    hass = MagicMock()
    hass.data = {DATA_MANAGER: manager}
    context = InspectionContext()

    await BackupCollector().collect(hass, context)

    assert context.backups.count == 3
    assert context.backups.latest == valid_date.isoformat()
    assert context.backups.oldest == valid_date.isoformat()


class _BrokenRecords:
    def to_list(self) -> list[dict[str, object]]:
        """Simulate an incompatible system-log record store."""
        raise TypeError


@pytest.mark.parametrize(
    ("handler", "now"),
    [
        (SimpleNamespace(records=_BrokenRecords()), datetime.now(UTC)),
        (
            SimpleNamespace(
                records=SimpleNamespace(
                    to_list=lambda: [
                        {"timestamp": "bad", "level": "ERROR"},
                        {"timestamp": datetime.now(UTC).timestamp(), "level": 5},
                    ]
                )
            ),
            datetime.now(UTC).replace(tzinfo=None),
        ),
    ],
)
def test_logs_defensive_inputs(handler, now: datetime) -> None:
    """Malformed log stores and entries are ignored safely."""
    hass = SimpleNamespace(data={"system_log": handler})

    state = _collect_logs_state(hass, now=now)

    assert state.available is False or state.error_entries == 0


def test_logs_uses_current_time_when_not_supplied() -> None:
    """The log collector can establish its own UTC reference time."""
    hass = SimpleNamespace(
        data={
            "system_log": SimpleNamespace(
                records=SimpleNamespace(to_list=lambda: [])
            )
        }
    )

    state = _collect_logs_state(hass)

    assert state.available is True


def test_database_size_without_dialect() -> None:
    """Recorder size is unavailable without a database dialect."""
    recorder = SimpleNamespace(dialect_name=None)

    assert recorder_module._database_size_bytes(recorder) is None


def test_database_size_without_supported_size_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unsupported database dialects have no size estimate."""
    monkeypatch.setattr(recorder_module, "DIALECT_TO_GET_SIZE", {})
    recorder = SimpleNamespace(dialect_name="unsupported")

    assert recorder_module._database_size_bytes(recorder) is None


def test_database_size_query_returning_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A database size query may legitimately return no value."""

    class FakeSessionContext:
        def __enter__(self):
            return object()

        def __exit__(self, exc_type, exc, tb):
            return False

    recorder = SimpleNamespace(
        dialect_name="sqlite",
        db_url="sqlite:///config/home-assistant_v2.db",
        get_session=lambda: object(),
    )

    monkeypatch.setattr(
        recorder_module,
        "DIALECT_TO_GET_SIZE",
        {"sqlite": lambda session, database_name: None},
    )
    monkeypatch.setattr(
        recorder_module,
        "session_scope",
        lambda *, session, read_only: FakeSessionContext(),
    )

    assert recorder_module._database_size_bytes(recorder) is None


def test_repairs_unavailable_without_issue_registry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing Repairs support produces an unavailable state."""
    _block_import(
        monkeypatch,
        module="homeassistant.helpers",
        from_name="issue_registry",
    )

    state = repairs_module._collect_repairs_state(SimpleNamespace())

    assert state.available is False


def test_network_connectivity_without_hassio(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Network state is unknown when Supervisor support is unavailable."""
    _block_import(
        monkeypatch,
        module="homeassistant.components.hassio.coordinator",
    )

    assert system_module._collect_network_connectivity(
        SimpleNamespace()
    ) == (None, None)


def test_network_connectivity_when_supervisor_not_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Network state is unknown while Supervisor is not ready."""
    class FakeNotReadyError(Exception):
        pass

    monkeypatch.setitem(
        __import__("sys").modules,
        "homeassistant.components.hassio.coordinator",
        SimpleNamespace(
            get_network_info=lambda hass: (_ for _ in ()).throw(
                FakeNotReadyError()
            )
        ),
    )
    monkeypatch.setitem(
        __import__("sys").modules,
        "homeassistant.components.hassio.exceptions",
        SimpleNamespace(HassioNotReadyError=FakeNotReadyError),
    )

    assert system_module._collect_network_connectivity(
        SimpleNamespace()
    ) == (None, None)


def test_network_connectivity_rejects_non_boolean_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unexpected Supervisor network values are normalized to unknown."""
    monkeypatch.setitem(
        __import__("sys").modules,
        "homeassistant.components.hassio.coordinator",
        SimpleNamespace(
            get_network_info=lambda hass: {
                "host_internet": "yes",
                "supervisor_internet": 1,
            }
        ),
    )
    monkeypatch.setitem(
        __import__("sys").modules,
        "homeassistant.components.hassio.exceptions",
        SimpleNamespace(HassioNotReadyError=RuntimeError),
    )

    assert system_module._collect_network_connectivity(
        SimpleNamespace()
    ) == (None, None)


def test_time_synchronization_without_hassio(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Time synchronization is unknown without Supervisor support."""
    _block_import(
        monkeypatch,
        module="homeassistant.components.hassio.coordinator",
    )

    assert system_module._collect_time_synchronization(
        SimpleNamespace()
    ) is None


def test_time_synchronization_when_supervisor_not_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Time synchronization is unknown while Supervisor is not ready."""
    class FakeNotReadyError(Exception):
        pass

    monkeypatch.setitem(
        __import__("sys").modules,
        "homeassistant.components.hassio.coordinator",
        SimpleNamespace(
            get_host_info=lambda hass: (_ for _ in ()).throw(
                FakeNotReadyError()
            )
        ),
    )
    monkeypatch.setitem(
        __import__("sys").modules,
        "homeassistant.components.hassio.exceptions",
        SimpleNamespace(HassioNotReadyError=FakeNotReadyError),
    )

    assert system_module._collect_time_synchronization(
        SimpleNamespace()
    ) is None


def test_time_synchronization_accepts_boolean(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Boolean Supervisor synchronization values are preserved."""
    monkeypatch.setitem(
        __import__("sys").modules,
        "homeassistant.components.hassio.coordinator",
        SimpleNamespace(
            get_host_info=lambda hass: {"dt_synchronized": True}
        ),
    )
    monkeypatch.setitem(
        __import__("sys").modules,
        "homeassistant.components.hassio.exceptions",
        SimpleNamespace(HassioNotReadyError=RuntimeError),
    )

    assert system_module._collect_time_synchronization(
        SimpleNamespace()
    ) is True


def test_time_synchronization_rejects_non_boolean(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unexpected synchronization values are normalized to unknown."""
    monkeypatch.setitem(
        __import__("sys").modules,
        "homeassistant.components.hassio.coordinator",
        SimpleNamespace(
            get_host_info=lambda hass: {"dt_synchronized": "yes"}
        ),
    )
    monkeypatch.setitem(
        __import__("sys").modules,
        "homeassistant.components.hassio.exceptions",
        SimpleNamespace(HassioNotReadyError=RuntimeError),
    )

    assert system_module._collect_time_synchronization(
        SimpleNamespace()
    ) is None


@pytest.mark.asyncio
async def test_restart_history_handles_invalid_and_naive_timestamps() -> None:
    """Persisted malformed timestamps are skipped and naive ones get UTC."""
    history = RestartHistory(MagicMock())
    history._store.async_load = AsyncMock(
        return_value={
            "starts": [
                "invalid",
                "2026-08-22T06:00:00",
            ]
        }
    )

    await history.async_load()

    assert all(value.tzinfo is not None for value in history._starts)


@pytest.mark.asyncio
async def test_restart_history_default_and_naive_record_times() -> None:
    """Recording supports both implicit current time and naive time."""
    history = RestartHistory(MagicMock())
    history._store.async_save = AsyncMock()

    await history.async_record_start()
    await history.async_record_start(datetime(2026, 8, 22, 6, 0))

    assert len(history._starts) >= 1


def test_restart_counts_default_and_naive_times() -> None:
    """Restart counting supports implicit current time and naive time."""
    history = RestartHistory(MagicMock())

    current = history.restart_counts()
    naive = history.restart_counts(datetime(2026, 8, 22, 6, 0))

    assert len(current) == 2
    assert len(naive) == 2
