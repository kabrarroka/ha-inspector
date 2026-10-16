"""Tests for periodic inspection scheduling."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

from custom_components.ha_inspector.periodic_inspection import (
    PeriodicInspectionScheduler,
)


async def test_scheduler_starts_disabled() -> None:
    """The scheduler must not start automatically."""
    run_inspection = AsyncMock()

    scheduler = PeriodicInspectionScheduler(
        interval_minutes=60,
        run_inspection=run_inspection,
    )

    assert not scheduler.running
    run_inspection.assert_not_awaited()


async def test_scheduler_waits_before_first_inspection() -> None:
    """The first inspection must wait for the configured interval."""
    run_inspection = AsyncMock()
    sleep_started = asyncio.Event()
    release_sleep = asyncio.Event()

    async def fake_sleep(seconds: float) -> None:
        assert seconds == 300
        sleep_started.set()
        await release_sleep.wait()

    scheduler = PeriodicInspectionScheduler(
        interval_minutes=5,
        run_inspection=run_inspection,
    )

    with patch(
        "custom_components.ha_inspector.periodic_inspection.asyncio.sleep",
        side_effect=fake_sleep,
    ):
        scheduler.start()

        try:
            await asyncio.wait_for(sleep_started.wait(), timeout=2)

            assert scheduler.running
            run_inspection.assert_not_awaited()

        finally:
            await scheduler.stop()

    assert not scheduler.running
    run_inspection.assert_not_awaited()


async def test_scheduler_start_is_idempotent() -> None:
    """Starting twice must not create multiple scheduler tasks."""
    run_inspection = AsyncMock()
    sleep_started = asyncio.Event()
    release_sleep = asyncio.Event()
    sleep_calls = 0

    async def fake_sleep(seconds: float) -> None:
        nonlocal sleep_calls

        sleep_calls += 1
        sleep_started.set()
        await release_sleep.wait()

    scheduler = PeriodicInspectionScheduler(
        interval_minutes=60,
        run_inspection=run_inspection,
    )

    with patch(
        "custom_components.ha_inspector.periodic_inspection.asyncio.sleep",
        side_effect=fake_sleep,
    ):
        scheduler.start()
        scheduler.start()

        try:
            await asyncio.wait_for(sleep_started.wait(), timeout=2)

            assert scheduler.running
            assert sleep_calls == 1

        finally:
            await scheduler.stop()

    assert not scheduler.running


async def test_scheduler_stop_prevents_inspections() -> None:
    """Stopping during the wait must prevent an inspection."""
    run_inspection = AsyncMock()
    sleep_started = asyncio.Event()
    release_sleep = asyncio.Event()

    async def fake_sleep(seconds: float) -> None:
        sleep_started.set()
        await release_sleep.wait()

    scheduler = PeriodicInspectionScheduler(
        interval_minutes=60,
        run_inspection=run_inspection,
    )

    with patch(
        "custom_components.ha_inspector.periodic_inspection.asyncio.sleep",
        side_effect=fake_sleep,
    ):
        scheduler.start()

        await asyncio.wait_for(sleep_started.wait(), timeout=2)
        await scheduler.stop()

    assert not scheduler.running
    run_inspection.assert_not_awaited()


async def test_scheduler_runs_repeatedly_without_overlap() -> None:
    """Each interval runs an inspection after the previous one finishes."""
    sleep_started: asyncio.Queue[None] = asyncio.Queue()
    sleep_releases: asyncio.Queue[asyncio.Event] = asyncio.Queue()
    inspection_started: asyncio.Queue[None] = asyncio.Queue()
    inspection_releases: asyncio.Queue[asyncio.Event] = asyncio.Queue()

    active_inspections = 0
    maximum_active = 0

    async def fake_sleep(seconds: float) -> None:
        """Wait until the test releases the next interval."""
        assert seconds == 300

        release = asyncio.Event()
        await sleep_releases.put(release)
        await sleep_started.put(None)

        await release.wait()

    async def run_inspection() -> None:
        """Simulate an inspection that can take time."""
        nonlocal active_inspections, maximum_active

        active_inspections += 1
        maximum_active = max(maximum_active, active_inspections)

        release = asyncio.Event()

        try:
            await inspection_releases.put(release)
            await inspection_started.put(None)
            await release.wait()
        finally:
            active_inspections -= 1

    scheduler = PeriodicInspectionScheduler(
        interval_minutes=5,
        run_inspection=run_inspection,
    )

    with patch(
        "custom_components.ha_inspector.periodic_inspection.asyncio.sleep",
        side_effect=fake_sleep,
    ):
        scheduler.start()

        try:
            # First interval.
            await asyncio.wait_for(sleep_started.get(), timeout=2)
            first_sleep = sleep_releases.get_nowait()

            assert active_inspections == 0

            first_sleep.set()

            await asyncio.wait_for(inspection_started.get(), timeout=2)
            first_inspection = inspection_releases.get_nowait()

            assert active_inspections == 1
            assert maximum_active == 1

            # No second interval begins while inspection is active.
            assert sleep_started.empty()

            first_inspection.set()

            # Second interval.
            await asyncio.wait_for(sleep_started.get(), timeout=2)
            second_sleep = sleep_releases.get_nowait()

            assert active_inspections == 0

            second_sleep.set()

            await asyncio.wait_for(inspection_started.get(), timeout=2)
            second_inspection = inspection_releases.get_nowait()

            assert active_inspections == 1
            assert maximum_active == 1

            second_inspection.set()

            # The scheduler continues after the second inspection.
            await asyncio.wait_for(sleep_started.get(), timeout=2)

        finally:
            await scheduler.stop()

    assert not scheduler.running
    assert active_inspections == 0
    assert maximum_active == 1


async def test_scheduler_stop_cancels_active_inspection() -> None:
    """Stopping must cancel an inspection currently in progress."""
    inspection_started = asyncio.Event()
    inspection_cancelled = asyncio.Event()
    release_inspection = asyncio.Event()
    inspection_calls = 0

    async def fake_sleep(seconds: float) -> None:
        """Allow the first scheduling interval to finish immediately."""
        assert seconds == 300

    async def run_inspection() -> None:
        """Simulate an inspection that remains active until cancelled."""
        nonlocal inspection_calls

        inspection_calls += 1
        inspection_started.set()

        try:
            await release_inspection.wait()
        except asyncio.CancelledError:
            inspection_cancelled.set()
            raise

    scheduler = PeriodicInspectionScheduler(
        interval_minutes=5,
        run_inspection=run_inspection,
    )

    with patch(
        "custom_components.ha_inspector.periodic_inspection.asyncio.sleep",
        side_effect=fake_sleep,
    ):
        scheduler.start()

        try:
            await asyncio.wait_for(
                inspection_started.wait(),
                timeout=2,
            )

            assert scheduler.running
            assert inspection_calls == 1

            await asyncio.wait_for(
                scheduler.stop(),
                timeout=2,
            )

            assert inspection_cancelled.is_set()
            assert not scheduler.running
            assert inspection_calls == 1

        finally:
            release_inspection.set()
            await scheduler.stop()


async def test_scheduler_recovers_after_inspection_failure() -> None:
    """An inspection failure must not stop subsequent scheduled runs."""
    from unittest.mock import MagicMock

    inspection_calls = 0
    second_inspection_completed = asyncio.Event()
    second_interval_started = asyncio.Event()
    release_second_interval = asyncio.Event()

    async def fake_sleep(seconds: float) -> None:
        """Control scheduling intervals without real delays."""
        assert seconds == 300

        if inspection_calls == 1:
            second_interval_started.set()
            await release_second_interval.wait()

    async def run_inspection() -> None:
        """Fail once and succeed on the following inspection."""
        nonlocal inspection_calls

        inspection_calls += 1

        if inspection_calls == 1:
            raise RuntimeError("Simulated inspection failure")

        second_inspection_completed.set()

    scheduler = PeriodicInspectionScheduler(
        interval_minutes=5,
        run_inspection=run_inspection,
    )

    logger = MagicMock()

    with (
        patch(
            "custom_components.ha_inspector.periodic_inspection.asyncio.sleep",
            side_effect=fake_sleep,
        ),
        patch(
            "custom_components.ha_inspector.periodic_inspection._LOGGER",
            logger,
        ),
    ):
        scheduler.start()

        try:
            await asyncio.wait_for(
                second_interval_started.wait(),
                timeout=2,
            )

            assert inspection_calls == 1
            assert scheduler.running

            logger.exception.assert_called_once_with(
                "Periodic HA Inspector inspection failed"
            )

            release_second_interval.set()

            await asyncio.wait_for(
                second_inspection_completed.wait(),
                timeout=2,
            )

            assert inspection_calls >= 2
            assert scheduler.running

        finally:
            await scheduler.stop()

    assert not scheduler.running
    logger.exception.assert_called_once()
