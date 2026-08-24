"""Tests for acknowledgement management services."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
import voluptuous as vol

from custom_components.ha_inspector import (
    SERVICE_ACKNOWLEDGE_FINDING_SCHEMA,
    SERVICE_CLEAR_ACKNOWLEDGEMENT_SCHEMA,
    SERVICE_CLEAR_ACKNOWLEDGEMENTS_SCHEMA,
    SERVICE_LIST_ACKNOWLEDGEMENTS_SCHEMA,
    async_setup,
)
from custom_components.ha_inspector.const import (
    DATA_ACKNOWLEDGEMENTS,
    DOMAIN,
)


async def _setup_services(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[MagicMock, dict[str, object]]:
    inspector_type = MagicMock()
    registry = MagicMock()

    monkeypatch.setattr(
        "custom_components.ha_inspector._load_engine",
        lambda: (inspector_type, registry),
    )

    hass = MagicMock()
    hass.data = {}
    hass.async_add_executor_job = AsyncMock(
        return_value=(inspector_type, registry)
    )

    await async_setup(hass, {})

    registrations = {
        call.args[1]: call.args[2]
        for call in hass.services.async_register.call_args_list
        if call.args[0] == DOMAIN
    }
    return hass, registrations


@pytest.mark.asyncio
async def test_acknowledgement_services_are_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """All acknowledgement management services are registered."""
    _, registrations = await _setup_services(monkeypatch)

    assert {
        "list_acknowledgements",
        "acknowledge_finding",
        "clear_acknowledgement",
        "clear_acknowledgements",
    } <= set(registrations)


@pytest.mark.asyncio
async def test_list_acknowledgements_returns_sorted_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Listing acknowledgements returns stable sorted output."""
    hass, registrations = await _setup_services(monkeypatch)

    store = MagicMock()
    store.finding_ids = frozenset({"RULE.B", "RULE.A"})
    hass.data[DOMAIN] = {DATA_ACKNOWLEDGEMENTS: store}

    response = await registrations["list_acknowledgements"](
        MagicMock()
    )

    assert response == {
        "finding_ids": ["RULE.A", "RULE.B"],
        "count": 2,
    }


@pytest.mark.asyncio
async def test_acknowledge_finding_updates_store(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Acknowledging a finding persists it and returns current state."""
    hass, registrations = await _setup_services(monkeypatch)

    finding_ids: set[str] = set()
    store = MagicMock()
    store.async_acknowledge = AsyncMock(
        side_effect=lambda finding_id: finding_ids.add(finding_id)
    )
    type(store).finding_ids = property(
        lambda self: frozenset(finding_ids)
    )
    hass.data[DOMAIN] = {DATA_ACKNOWLEDGEMENTS: store}

    call = MagicMock()
    call.data = {"finding_id": "RULE.1"}

    response = await registrations["acknowledge_finding"](call)

    store.async_acknowledge.assert_awaited_once_with("RULE.1")
    assert response == {
        "finding_ids": ["RULE.1"],
        "count": 1,
    }


@pytest.mark.asyncio
async def test_clear_acknowledgement_updates_store(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Clearing one acknowledgement persists the new state."""
    hass, registrations = await _setup_services(monkeypatch)

    finding_ids = {"RULE.1", "RULE.2"}
    store = MagicMock()
    store.async_clear = AsyncMock(
        side_effect=lambda finding_id: finding_ids.discard(finding_id)
    )
    type(store).finding_ids = property(
        lambda self: frozenset(finding_ids)
    )
    hass.data[DOMAIN] = {DATA_ACKNOWLEDGEMENTS: store}

    call = MagicMock()
    call.data = {"finding_id": "RULE.1"}

    response = await registrations["clear_acknowledgement"](call)

    store.async_clear.assert_awaited_once_with("RULE.1")
    assert response == {
        "finding_ids": ["RULE.2"],
        "count": 1,
    }


@pytest.mark.asyncio
async def test_clear_acknowledgements_updates_store(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Clearing all acknowledgements returns an empty state."""
    hass, registrations = await _setup_services(monkeypatch)

    finding_ids = {"RULE.1", "RULE.2"}

    async def clear_all() -> None:
        finding_ids.clear()

    store = MagicMock()
    store.async_clear_all = AsyncMock(side_effect=clear_all)
    type(store).finding_ids = property(
        lambda self: frozenset(finding_ids)
    )
    hass.data[DOMAIN] = {DATA_ACKNOWLEDGEMENTS: store}

    response = await registrations["clear_acknowledgements"](
        MagicMock()
    )

    store.async_clear_all.assert_awaited_once_with()
    assert response == {
        "finding_ids": [],
        "count": 0,
    }


@pytest.mark.asyncio
async def test_acknowledgement_service_requires_initialized_store(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Acknowledgement services fail clearly before entry setup."""
    _, registrations = await _setup_services(monkeypatch)

    with pytest.raises(
        RuntimeError,
        match="acknowledgement store is not initialized",
    ):
        await registrations["list_acknowledgements"](MagicMock())


def test_acknowledgement_service_schemas() -> None:
    """Acknowledgement schemas accept only their documented fields."""
    assert SERVICE_LIST_ACKNOWLEDGEMENTS_SCHEMA({}) == {}
    assert SERVICE_CLEAR_ACKNOWLEDGEMENTS_SCHEMA({}) == {}

    assert SERVICE_ACKNOWLEDGE_FINDING_SCHEMA(
        {"finding_id": "RULE.1"}
    ) == {"finding_id": "RULE.1"}

    assert SERVICE_CLEAR_ACKNOWLEDGEMENT_SCHEMA(
        {"finding_id": "RULE.1"}
    ) == {"finding_id": "RULE.1"}

    with pytest.raises(vol.MultipleInvalid):
        SERVICE_ACKNOWLEDGE_FINDING_SCHEMA({})

    with pytest.raises(vol.MultipleInvalid):
        SERVICE_CLEAR_ACKNOWLEDGEMENT_SCHEMA({})

    with pytest.raises(vol.MultipleInvalid):
        SERVICE_LIST_ACKNOWLEDGEMENTS_SCHEMA(
            {"unexpected": True}
        )
