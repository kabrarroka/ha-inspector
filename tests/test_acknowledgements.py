"""Tests for persistent finding acknowledgements."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.ha_inspector.engine.acknowledgements import (
    AcknowledgementStore,
)


@pytest.fixture
def store() -> tuple[AcknowledgementStore, MagicMock]:
    """Create an acknowledgement store with mocked HA storage."""
    hass = MagicMock()
    backing_store = MagicMock()
    backing_store.async_load = AsyncMock()
    backing_store.async_save = AsyncMock()

    with patch(
        "custom_components.ha_inspector.engine.acknowledgements.Store",
        return_value=backing_store,
    ):
        acknowledgements = AcknowledgementStore(hass)

    return acknowledgements, backing_store


@pytest.mark.asyncio
async def test_load_acknowledgements(
    store: tuple[AcknowledgementStore, MagicMock],
) -> None:
    acknowledgements, backing_store = store
    backing_store.async_load.return_value = {
        "finding_ids": [" B ", "A", "", 123],
    }

    await acknowledgements.async_load()

    assert acknowledgements.finding_ids == frozenset({"A", "B"})


@pytest.mark.asyncio
@pytest.mark.parametrize("data", [None, [], {}, {"finding_ids": "A"}])
async def test_load_ignores_invalid_data(
    store: tuple[AcknowledgementStore, MagicMock],
    data: object,
) -> None:
    acknowledgements, backing_store = store
    backing_store.async_load.return_value = data

    await acknowledgements.async_load()

    assert acknowledgements.finding_ids == frozenset()


@pytest.mark.asyncio
async def test_acknowledge_persists_sorted_ids(
    store: tuple[AcknowledgementStore, MagicMock],
) -> None:
    acknowledgements, backing_store = store

    await acknowledgements.async_acknowledge(" B ")
    await acknowledgements.async_acknowledge("A")

    assert acknowledgements.finding_ids == frozenset({"A", "B"})
    backing_store.async_save.assert_awaited_with(
        {"finding_ids": ["A", "B"]}
    )


@pytest.mark.asyncio
async def test_clear_acknowledgement(
    store: tuple[AcknowledgementStore, MagicMock],
) -> None:
    acknowledgements, backing_store = store

    await acknowledgements.async_acknowledge("A")
    await acknowledgements.async_clear(" A ")

    assert acknowledgements.finding_ids == frozenset()
    backing_store.async_save.assert_awaited_with({"finding_ids": []})


@pytest.mark.asyncio
async def test_clear_all_acknowledgements(
    store: tuple[AcknowledgementStore, MagicMock],
) -> None:
    acknowledgements, backing_store = store

    await acknowledgements.async_acknowledge("A")
    await acknowledgements.async_acknowledge("B")
    await acknowledgements.async_clear_all()

    assert acknowledgements.finding_ids == frozenset()
    backing_store.async_save.assert_awaited_with({"finding_ids": []})


@pytest.mark.asyncio
@pytest.mark.parametrize("method_name", ["async_acknowledge", "async_clear"])
async def test_empty_finding_id_is_rejected(
    store: tuple[AcknowledgementStore, MagicMock],
    method_name: str,
) -> None:
    acknowledgements, _ = store

    method = getattr(acknowledgements, method_name)

    with pytest.raises(ValueError, match="cannot be empty"):
        await method("   ")
