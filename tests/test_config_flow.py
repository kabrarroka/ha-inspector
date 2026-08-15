"""Tests for the HA Inspector config flow."""

from __future__ import annotations

import pytest

from custom_components.ha_inspector.config_flow import HAInspectorConfigFlow
from custom_components.ha_inspector.const import DOMAIN, NAME


@pytest.mark.asyncio
async def test_user_step_shows_form(monkeypatch: pytest.MonkeyPatch) -> None:
    flow = HAInspectorConfigFlow()

    unique_ids: list[str] = []

    async def async_set_unique_id(unique_id: str) -> None:
        unique_ids.append(unique_id)

    monkeypatch.setattr(flow, "async_set_unique_id", async_set_unique_id)
    monkeypatch.setattr(
        flow,
        "_abort_if_unique_id_configured",
        lambda: None,
    )
    monkeypatch.setattr(
        flow,
        "async_show_form",
        lambda **kwargs: kwargs,
    )

    result = await flow.async_step_user()

    assert unique_ids == [DOMAIN]
    assert result["step_id"] == "user"


@pytest.mark.asyncio
async def test_user_step_creates_entry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    flow = HAInspectorConfigFlow()

    async def async_set_unique_id(unique_id: str) -> None:
        assert unique_id == DOMAIN

    monkeypatch.setattr(flow, "async_set_unique_id", async_set_unique_id)
    monkeypatch.setattr(
        flow,
        "_abort_if_unique_id_configured",
        lambda: None,
    )
    monkeypatch.setattr(
        flow,
        "async_create_entry",
        lambda **kwargs: kwargs,
    )

    result = await flow.async_step_user({})

    assert result == {
        "title": NAME,
        "data": {},
    }