"""Inspection context shared between collectors and rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .backup_state import BackupState
from .entities_state import EntitiesState
from .i18n import DEFAULT_LANGUAGE
from .integrations_state import IntegrationsState
from .logs_state import LogsState
from .recorder_state import RecorderState
from .storage_state import StorageState
from .system_state import SystemState


@dataclass(slots=True)
class InspectionContext:
    """Contain all data collected during an inspection."""

    system: SystemState = field(default_factory=SystemState)
    storage: StorageState = field(default_factory=StorageState)
    logs: LogsState = field(default_factory=LogsState)
    backups: BackupState = field(default_factory=BackupState)
    recorder: RecorderState = field(default_factory=RecorderState)
    integrations: IntegrationsState = field(default_factory=IntegrationsState)
    entities: EntitiesState = field(default_factory=EntitiesState)
    metadata: dict[str, Any] = field(default_factory=dict)
    language: str = DEFAULT_LANGUAGE
