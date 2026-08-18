"""Recorder information collector for HA Inspector."""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlparse

from homeassistant.components.recorder.core import Recorder
from homeassistant.components.recorder.system_health import DIALECT_TO_GET_SIZE
from homeassistant.components.recorder.util import session_scope
from homeassistant.helpers.recorder import DATA_INSTANCE, get_instance

from ..context import InspectionContext
from ..recorder_state import RecorderState
from .base import BaseCollector

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


def _database_size_bytes(recorder: Recorder) -> int | None:
    """Return the estimated Recorder database size in bytes."""
    dialect = recorder.dialect_name

    if dialect is None:
        return None

    get_size = DIALECT_TO_GET_SIZE.get(dialect)

    if get_size is None:
        return None

    database_name = urlparse(recorder.db_url).path.lstrip("/")

    with session_scope(
        session=recorder.get_session(),
        read_only=True,
    ) as session:
        size = get_size(session, database_name)

    if size is None:
        return None

    return int(size)


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

            context.recorder = state
            return

        recorder = get_instance(hass)

        dialect = recorder.dialect_name

        database_size_bytes: int | None = None

        if (
            recorder.async_db_ready.done()
            and recorder.async_db_ready.result()
        ):
            database_size_bytes = await recorder.async_add_executor_job(
                _database_size_bytes,
                recorder,
            )

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
            database_size_bytes=database_size_bytes,
        )

        context.recorder = state
