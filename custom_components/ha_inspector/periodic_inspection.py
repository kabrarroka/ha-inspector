"""Periodic inspection scheduling for HA Inspector."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from contextlib import suppress

_LOGGER = logging.getLogger(__name__)


class PeriodicInspectionScheduler:
    """Run inspections periodically without overlapping executions."""

    def __init__(
        self,
        *,
        interval_minutes: int,
        run_inspection: Callable[[], Awaitable[None]],
    ) -> None:
        """Initialize the scheduler."""
        self._interval_minutes = interval_minutes
        self._run_inspection = run_inspection
        self._task: asyncio.Task[None] | None = None

    @property
    def running(self) -> bool:
        """Return whether the scheduler is active."""
        return self._task is not None and not self._task.done()

    def start(self) -> None:
        """Start periodic scheduling."""
        if self.running:
            return

        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        """Stop periodic scheduling and cancel pending work."""
        task = self._task

        if task is None:
            return

        self._task = None
        task.cancel()

        with suppress(asyncio.CancelledError):
            await task

    async def _run(self) -> None:
        """Execute inspections at the configured interval."""
        while True:
            await asyncio.sleep(self._interval_minutes * 60)

            try:
                await self._run_inspection()
            except asyncio.CancelledError:
                raise
            except Exception:
                _LOGGER.exception(
                    "Periodic HA Inspector inspection failed"
                )
