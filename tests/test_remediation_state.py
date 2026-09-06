"""Tests for persistent remediation lifecycle state."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ha_inspector.engine.remediation_state import (
    RemediationStateStore,
)


def _state() -> dict[str, object]:
    """Build representative persisted remediation state."""
    return {
        "progress": {
            "tracked_entities": 2,
            "pending": 1,
            "in_progress": 1,
            "resolved": 0,
            "total_actions": 3,
            "completed_actions": 1,
            "remaining_actions": 2,
            "new_references": 0,
            "entities": [
                {
                    "entity_id": "sensor.first",
                    "status": "in_progress",
                    "total_action_count": 2,
                    "completed_action_count": 1,
                    "remaining_action_count": 1,
                    "new_reference_count": 0,
                },
                {
                    "entity_id": "sensor.second",
                    "status": "pending",
                    "total_action_count": 1,
                    "completed_action_count": 0,
                    "remaining_action_count": 1,
                    "new_reference_count": 0,
                },
            ],
        },
        "lifecycle": {
            "status": "progressing",
            "tracked_entities": 2,
            "pending": 1,
            "in_progress": 1,
            "resolved": 0,
            "completed_actions": 1,
            "remaining_actions": 2,
            "new_references": 0,
            "resolved_since_previous": 0,
            "newly_pending_since_previous": 0,
            "new_references_delta": 0,
        },
    }


@pytest.mark.asyncio
async def test_load_empty_state() -> None:
    """Empty storage produces no persisted remediation state."""
    store = RemediationStateStore(MagicMock())
    store._store.async_load = AsyncMock(return_value=None)

    await store.async_load()

    assert store.state() is None


@pytest.mark.asyncio
async def test_set_state_persists_progress_and_lifecycle() -> None:
    """Persisted remediation state contains progress and lifecycle."""
    store = RemediationStateStore(MagicMock())
    store._store.async_load = AsyncMock(return_value=None)
    store._store.async_save = AsyncMock()

    await store.async_load()

    state = _state()
    await store.async_set(state)

    assert store.state() == state
    store._store.async_save.assert_awaited_once_with(state)


@pytest.mark.asyncio
async def test_load_restores_persisted_state() -> None:
    """Persisted remediation state is restored on load."""
    state = _state()

    store = RemediationStateStore(MagicMock())
    store._store.async_load = AsyncMock(return_value=state)

    await store.async_load()

    assert store.state() == state


def test_state_returns_copy() -> None:
    """Returned state cannot mutate the internal stored value."""
    store = RemediationStateStore(MagicMock())
    store._state = _state()

    state = store.state()
    assert state is not None

    progress = state["progress"]
    assert isinstance(progress, dict)
    progress["pending"] = 99

    restored = store.state()
    assert restored is not None
    assert restored["progress"]["pending"] == 1


@pytest.mark.asyncio
async def test_load_rejects_malformed_state() -> None:
    """Malformed persisted remediation state is ignored."""
    store = RemediationStateStore(MagicMock())
    store._store.async_load = AsyncMock(
        return_value={
            "progress": "invalid",
            "lifecycle": ["invalid"],
        }
    )

    await store.async_load()

    assert store.state() is None


@pytest.mark.asyncio
async def test_set_rejects_malformed_state() -> None:
    """Malformed remediation state cannot be persisted."""
    store = RemediationStateStore(MagicMock())
    store._store.async_save = AsyncMock()

    with pytest.raises(ValueError, match="Invalid remediation state"):
        await store.async_set(
            {
                "progress": "invalid",
                "lifecycle": {},
            }
        )

    store._store.async_save.assert_not_awaited()
