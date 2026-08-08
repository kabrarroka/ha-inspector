"""Recorder information collector for HA Inspector."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.recorder import DATA_INSTANCE, get_instance

from ..context import InspectionContext
from ..recorder_state import RecorderState
from .base import BaseCollector

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class RecorderCollector(BaseCollector):
    """Collect information about the Home Assistant recorder."""

    collector_id = "recorder"

    async def collect(
        self,
        hass: HomeAssistant,
        context: InspectionContext,
    ) -> None:
        """Collect recorder configuration and runtime information."""
        if DATA_INSTANCE not in hass.data:
            state = RecorderState(
                available=False,
                reason="Recorder instance is not available",
            )

            context.recorder.update(state.as_dict())
            return

        recorder = get_instance(hass)

        dialect = recorder.dialect_name

        state = RecorderState(
            available=True,
            enabled=recorder.enabled,
            recording=recorder.recording,
            is_running=recorder.is_running,
            auto_purge=recorder.auto_purge,
            auto_repack=recorder.auto_repack,
            keep_days=recorder.keep_days,
            commit_interval=recorder.commit_interval,
            backlog=recorder.backlog,
            schema_version=recorder.schema_version,
            migration_in_progress=recorder.migration_in_progress,
            migration_is_live=recorder.migration_is_live,
            database_dialect=(
                dialect.value
                if dialect is not None
                else None
            ),
            database_connected=(
                recorder.async_db_connected.done()
                and recorder.async_db_connected.result()
            ),
            database_ready=(
                recorder.async_db_ready.done()
                and recorder.async_db_ready.result()
            ),
        )

        context.recorder.update(state.as_dict())