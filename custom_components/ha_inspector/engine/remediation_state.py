"""Persistent remediation lifecycle state for HA Inspector."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any, Final, TypedDict

from homeassistant.helpers.storage import Store

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


_STORAGE_VERSION: Final = 1
_STORAGE_KEY: Final = "ha_inspector.remediation_state"


class RemediationState(TypedDict):
    """Persisted remediation progress and lifecycle state."""

    progress: dict[str, Any]
    lifecycle: dict[str, Any]


class RemediationStateStore:
    """Persist the latest public remediation state."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the remediation state store."""
        self._store = Store[dict[str, Any]](
            hass,
            _STORAGE_VERSION,
            _STORAGE_KEY,
        )
        self._state: RemediationState | None = None

    async def async_load(self) -> None:
        """Load persisted remediation state."""
        data = await self._store.async_load()

        if not isinstance(data, dict):
            self._state = None
            return

        progress = data.get("progress")
        lifecycle = data.get("lifecycle")

        if not isinstance(progress, dict) or not isinstance(lifecycle, dict):
            self._state = None
            return

        self._state = {
            "progress": deepcopy(progress),
            "lifecycle": deepcopy(lifecycle),
        }

    async def async_set(self, state: dict[str, object]) -> None:
        """Persist remediation progress and lifecycle state."""
        progress = state.get("progress")
        lifecycle = state.get("lifecycle")

        if not isinstance(progress, dict) or not isinstance(lifecycle, dict):
            raise ValueError("Invalid remediation state")

        normalized: RemediationState = {
            "progress": deepcopy(progress),
            "lifecycle": deepcopy(lifecycle),
        }

        self._state = normalized
        await self._store.async_save(deepcopy(normalized))

    def state(self) -> RemediationState | None:
        """Return a copy of the persisted remediation state."""
        return deepcopy(self._state)


__all__ = [
    "RemediationState",
    "RemediationStateStore",
]
