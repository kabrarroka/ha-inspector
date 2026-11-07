"""Tests for event-triggered HA Inspector inspections."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

from homeassistant.const import EVENT_HOMEASSISTANT_STARTED

from custom_components.ha_inspector.event_inspection import (
    EVENT_AUTOMATION_RELOADED,
    EventInspectionScheduler,
)


def create_scheduler(
    run_inspection: AsyncMock,
) -> tuple[EventInspectionScheduler, dict[str, object], list[MagicMock]]:
    """Create a scheduler with mocked Home Assistant listeners."""
    hass = MagicMock()
    listeners: dict[str, object] = {}
    unsubscribers: list[MagicMock] = []

    def listen(event_type: str, callback: object) -> MagicMock:
        listeners[event_type] = callback
        unsubscribe = MagicMock()
        unsubscribers.append(unsubscribe)
        return unsubscribe

    hass.bus.async_listen.side_effect = listen
    hass.async_create_task.side_effect = (
        lambda coroutine, name: asyncio.create_task(coroutine, name=name)
    )

    scheduler = EventInspectionScheduler(
        hass=hass,
        run_inspection=run_inspection,
        debounce_seconds=0.01,
    )

    return scheduler, listeners, unsubscribers


async def test_registers_and_removes_listeners() -> None:
    """Register both events and remove listeners on stop."""
    scheduler, listeners, unsubscribers = create_scheduler(
        AsyncMock(return_value=True)
    )

    scheduler.start()
    scheduler.start()

    assert scheduler.running
    assert set(listeners) == {
        EVENT_HOMEASSISTANT_STARTED,
        EVENT_AUTOMATION_RELOADED,
    }
    assert len(unsubscribers) == 2

    await scheduler.stop()

    assert not scheduler.running
    for unsubscribe in unsubscribers:
        unsubscribe.assert_called_once()


async def test_event_triggers_inspection() -> None:
    """An event schedules an inspection after debounce."""
    runner = AsyncMock(return_value=True)
    scheduler, listeners, _ = create_scheduler(runner)

    scheduler.start()
    callback = listeners[EVENT_AUTOMATION_RELOADED]
    assert callable(callback)

    callback(MagicMock())

    await asyncio.wait_for(
        wait_for_calls(runner, 1),
        timeout=1,
    )

    runner.assert_awaited_once()
    await scheduler.stop()


async def test_consecutive_events_are_grouped() -> None:
    """Events arriving together trigger one inspection."""
    runner = AsyncMock(return_value=True)
    scheduler, listeners, _ = create_scheduler(runner)

    scheduler.start()
    callback = listeners[EVENT_AUTOMATION_RELOADED]
    assert callable(callback)

    callback(MagicMock())
    callback(MagicMock())
    callback(MagicMock())

    await asyncio.wait_for(
        wait_for_calls(runner, 1),
        timeout=1,
    )

    assert runner.await_count == 1
    await scheduler.stop()


async def test_event_during_inspection_runs_again() -> None:
    """New events do not cancel an inspection already running."""
    entered = asyncio.Event()
    release = asyncio.Event()
    calls = 0

    async def run_inspection() -> bool:
        nonlocal calls
        calls += 1
        if calls == 1:
            entered.set()
            await release.wait()
        return True

    scheduler, listeners, _ = create_scheduler(
        AsyncMock(side_effect=run_inspection)
    )

    scheduler.start()
    callback = listeners[EVENT_AUTOMATION_RELOADED]
    assert callable(callback)

    callback(MagicMock())

    try:
        await asyncio.wait_for(entered.wait(), timeout=1)

        callback(MagicMock())
        assert calls == 1

        release.set()

        async def wait_for_second_run() -> None:
            while calls < 2:
                await asyncio.sleep(0.001)

        await asyncio.wait_for(wait_for_second_run(), timeout=1)

        assert calls == 2
    finally:
        release.set()
        await scheduler.stop()


async def test_stop_cancels_pending_inspection() -> None:
    """Stopping the scheduler cancels a pending inspection."""
    runner = AsyncMock(return_value=True)
    scheduler, listeners, _ = create_scheduler(runner)

    scheduler.start()
    callback = listeners[EVENT_AUTOMATION_RELOADED]
    assert callable(callback)

    callback(MagicMock())
    await scheduler.stop()

    runner.assert_not_awaited()


async def test_stop_during_inspection_does_not_cancel_runner() -> None:
    """Stopping event monitoring must not cancel an active inspection."""
    entered = asyncio.Event()
    release = asyncio.Event()
    completed = asyncio.Event()
    cancelled = False

    async def run_inspection() -> bool:
        nonlocal cancelled
        entered.set()

        try:
            await release.wait()
        except asyncio.CancelledError:
            cancelled = True
            raise

        completed.set()
        return True

    scheduler, listeners, _ = create_scheduler(
        AsyncMock(side_effect=run_inspection)
    )

    scheduler.start()
    callback = listeners[EVENT_AUTOMATION_RELOADED]
    assert callable(callback)

    callback(MagicMock())

    try:
        await asyncio.wait_for(entered.wait(), timeout=1)

        stop_task = asyncio.create_task(scheduler.stop())

        try:
            await asyncio.sleep(0)

            assert not cancelled
            assert not stop_task.done()

            release.set()

            await asyncio.wait_for(stop_task, timeout=1)
            await asyncio.wait_for(completed.wait(), timeout=1)

            assert not cancelled
        finally:
            release.set()
            if not stop_task.done():
                await asyncio.wait_for(stop_task, timeout=1)
    finally:
        release.set()


async def wait_for_calls(runner: AsyncMock, count: int) -> None:
    """Wait cooperatively until the runner reaches a call count."""
    while runner.await_count < count:
        await asyncio.sleep(0.001)


async def test_event_scheduler_restart_does_not_duplicate_listeners() -> None:
    """Restarting monitoring must not accumulate event listeners."""
    from unittest.mock import MagicMock

    from custom_components.ha_inspector.event_inspection import (
        EventInspectionScheduler,
    )

    hass = MagicMock()

    active_listeners: list[MagicMock] = []
    registered_events: list[str] = []

    def register_listener(
        event_type: str,
        callback: object,
    ) -> MagicMock:
        registered_events.append(event_type)

        unsubscribe = MagicMock()
        active_listeners.append(unsubscribe)

        return unsubscribe

    hass.bus.async_listen.side_effect = register_listener

    runner = AsyncMock(return_value=True)

    scheduler = EventInspectionScheduler(
        hass=hass,
        run_inspection=runner,
        debounce_seconds=0.01,
    )

    scheduler.start()

    assert scheduler.running is True
    assert len(active_listeners) == 2
    assert len(registered_events) == 2

    # Starting twice must not register duplicate listeners.
    scheduler.start()

    assert len(active_listeners) == 2

    await scheduler.stop()

    assert scheduler.running is False

    for unsubscribe in active_listeners:
        unsubscribe.assert_called_once()

    # Restart monitoring.
    scheduler.start()

    assert scheduler.running is True
    assert len(active_listeners) == 4
    assert len(registered_events) == 4

    await scheduler.stop()

    for unsubscribe in active_listeners:
        unsubscribe.assert_called_once()

    # Stopping twice must be safe.
    await scheduler.stop()

    for unsubscribe in active_listeners:
        unsubscribe.assert_called_once()



async def test_event_scheduler_handles_busy_inspection_runner() -> None:
    """Busy inspection runners must not prevent later event inspections."""
    import asyncio
    from unittest.mock import MagicMock

    from custom_components.ha_inspector.event_inspection import (
        EVENT_AUTOMATION_RELOADED,
        EventInspectionScheduler,
    )

    hass = MagicMock()

    listeners: dict[str, object] = {}

    def register_listener(
        event_type: str,
        callback: object,
    ) -> MagicMock:
        listeners[event_type] = callback
        return MagicMock()

    hass.bus.async_listen.side_effect = register_listener

    hass.async_create_task.side_effect = (
        lambda coroutine, name: asyncio.create_task(
            coroutine,
            name=name,
        )
    )

    runner = AsyncMock(side_effect=[False, True])

    scheduler = EventInspectionScheduler(
        hass=hass,
        run_inspection=runner,
        debounce_seconds=0.01,
    )

    scheduler.start()

    callback = listeners[EVENT_AUTOMATION_RELOADED]

    assert callable(callback)

    callback(MagicMock())

    await asyncio.sleep(0.05)

    assert runner.await_count == 1
    assert runner.await_args_list[0].args == ()

    callback(MagicMock())

    await asyncio.sleep(0.05)

    assert runner.await_count == 2

    await scheduler.stop()

    assert scheduler.running is False
