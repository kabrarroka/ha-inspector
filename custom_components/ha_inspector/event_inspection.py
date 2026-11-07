"""Event-triggered automatic inspections for HA Inspector."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from contextlib import suppress

from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import Event, HomeAssistant

_LOGGER = logging.getLogger(__name__)

EVENT_AUTOMATION_RELOADED = "automation_reloaded"

DEFAULT_EVENT_DEBOUNCE_SECONDS = 10


class EventInspectionScheduler:
    """Schedule inspections in response to Home Assistant events."""

    def __init__(
        self,
        *,
        hass: HomeAssistant,
        run_inspection: Callable[[], Awaitable[bool]],
        debounce_seconds: float = DEFAULT_EVENT_DEBOUNCE_SECONDS,
    ) -> None:
        """Initialize the event inspection scheduler."""
        self._hass = hass
        self._run_inspection = run_inspection
        self._debounce_seconds = debounce_seconds
        self._unsubscribers: list[Callable[[], None]] = []
        self._task: asyncio.Task[None] | None = None
        self._inspection_task: asyncio.Task[bool] | None = None
        self._active = False
        self._inspecting = False
        self._pending = False

    @property
    def running(self) -> bool:
        """Return whether event monitoring is active."""
        return self._active

    def start(self) -> None:
        """Register event listeners."""
        if self._active:
            return

        self._active = True

        for event_type in (
            EVENT_HOMEASSISTANT_STARTED,
            EVENT_AUTOMATION_RELOADED,
        ):
            unsubscribe = self._hass.bus.async_listen(
                event_type,
                self._handle_event,
            )
            self._unsubscribers.append(unsubscribe)

    def _handle_event(self, event: Event) -> None:
        """Schedule an inspection after the debounce interval."""
        if not self._active:
            return

        if self._inspecting:
            self._pending = True
            return

        if self._task is not None and not self._task.done():
            self._task.cancel()

        self._task = self._hass.async_create_task(
            self._delayed_inspection(),
            "ha_inspector_event_inspection",
        )

    async def _delayed_inspection(self) -> None:
        """Wait for events to settle before inspecting."""
        try:
            await asyncio.sleep(self._debounce_seconds)

            self._inspecting = True

            while self._active:
                self._pending = False

                try:
                    self._inspection_task = asyncio.create_task(
                        self._execute_inspection()
                    )
                    await asyncio.shield(self._inspection_task)
                except asyncio.CancelledError:
                    raise
                except Exception:
                    _LOGGER.exception(
                        "Event-triggered HA Inspector inspection failed"
                    )
                finally:
                    if (
                        self._inspection_task is not None
                        and self._inspection_task.done()
                    ):
                        self._inspection_task = None

                if not self._pending:
                    break

                await asyncio.sleep(self._debounce_seconds)

        except asyncio.CancelledError:
            raise
        finally:
            self._inspecting = False

    async def _execute_inspection(self) -> bool:
        """Execute the configured inspection runner."""
        return await self._run_inspection()

    async def stop(self) -> None:
        """Remove listeners and cancel pending inspections."""
        self._active = False
        self._pending = False

        for unsubscribe in self._unsubscribers:
            unsubscribe()

        self._unsubscribers.clear()

        task = self._task
        self._task = None

        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

        inspection_task = self._inspection_task

        if inspection_task is not None:
            try:
                await inspection_task
            except asyncio.CancelledError:
                raise
            except Exception:
                _LOGGER.exception(
                    "Event-triggered HA Inspector inspection failed"
                )
            finally:
                self._inspection_task = None
