"""Tests for the HA Inspector config flow."""

from __future__ import annotations

import pytest

from custom_components.ha_inspector.config_flow import HAInspectorConfigFlow
from custom_components.ha_inspector.const import DOMAIN, NAME


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

def test_options_flow_creation() -> None:
    """The config flow exposes an options flow."""
    from unittest.mock import MagicMock

    from custom_components.ha_inspector.config_flow import (
        HAInspectorOptionsFlow,
    )

    entry = MagicMock()
    entry.options = {}

    options_flow = HAInspectorConfigFlow.async_get_options_flow(entry)

    assert isinstance(options_flow, HAInspectorOptionsFlow)


async def test_options_flow_default_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The options form uses safe defaults."""
    from unittest.mock import MagicMock

    from custom_components.ha_inspector.config_flow import (
        HAInspectorOptionsFlow,
    )
    from custom_components.ha_inspector.const import (
        CONF_PERIODIC_INSPECTION_ENABLED,
        CONF_PERIODIC_INSPECTION_INTERVAL,
        CONF_PERIODIC_INSPECTION_PROFILE,
    )

    entry = MagicMock()
    entry.options = {}

    flow = HAInspectorOptionsFlow()

    monkeypatch.setattr(
        type(flow),
        "config_entry",
        property(lambda self: entry),
    )

    monkeypatch.setattr(
        flow,
        "async_show_form",
        lambda **kwargs: kwargs,
    )

    result = await flow.async_step_init()

    assert result["step_id"] == "init"

    schema = result["data_schema"]
    options = schema({})

    assert options[CONF_PERIODIC_INSPECTION_ENABLED] is False
    assert options[CONF_PERIODIC_INSPECTION_INTERVAL] == 60
    assert options[CONF_PERIODIC_INSPECTION_PROFILE] == "quick"


async def test_options_flow_preserves_saved_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The options form restores previously saved settings."""
    from unittest.mock import MagicMock

    from custom_components.ha_inspector.config_flow import (
        HAInspectorOptionsFlow,
    )
    from custom_components.ha_inspector.const import (
        CONF_PERIODIC_INSPECTION_ENABLED,
        CONF_PERIODIC_INSPECTION_INTERVAL,
        CONF_PERIODIC_INSPECTION_PROFILE,
    )

    entry = MagicMock()
    entry.options = {
        CONF_PERIODIC_INSPECTION_ENABLED: True,
        CONF_PERIODIC_INSPECTION_INTERVAL: 30,
        CONF_PERIODIC_INSPECTION_PROFILE: "quick",
    }

    flow = HAInspectorOptionsFlow()

    monkeypatch.setattr(
        type(flow),
        "config_entry",
        property(lambda self: entry),
    )

    monkeypatch.setattr(
        flow,
        "async_show_form",
        lambda **kwargs: kwargs,
    )

    result = await flow.async_step_init()
    options = result["data_schema"]({})

    assert options == entry.options


@pytest.mark.parametrize("interval", [5, 1440])  # type: ignore[untyped-decorator]
async def test_options_flow_accepts_interval_limits(
    monkeypatch: pytest.MonkeyPatch,
    interval: int,
) -> None:
    """The minimum and maximum intervals are accepted."""
    from unittest.mock import MagicMock

    from custom_components.ha_inspector.config_flow import (
        HAInspectorOptionsFlow,
    )
    from custom_components.ha_inspector.const import (
        CONF_PERIODIC_INSPECTION_ENABLED,
        CONF_PERIODIC_INSPECTION_INTERVAL,
        CONF_PERIODIC_INSPECTION_PROFILE,
    )

    entry = MagicMock()
    entry.options = {}

    flow = HAInspectorOptionsFlow()

    monkeypatch.setattr(
        type(flow),
        "config_entry",
        property(lambda self: entry),
    )

    monkeypatch.setattr(
        flow,
        "async_create_entry",
        lambda **kwargs: kwargs,
    )

    result = await flow.async_step_init(
        {
            CONF_PERIODIC_INSPECTION_ENABLED: True,
            CONF_PERIODIC_INSPECTION_INTERVAL: interval,
            CONF_PERIODIC_INSPECTION_PROFILE: "quick",
        }
    )

    assert result["data"][CONF_PERIODIC_INSPECTION_INTERVAL] == interval


@pytest.mark.parametrize("interval", [4, 1441])  # type: ignore[untyped-decorator]
async def test_options_flow_rejects_invalid_intervals(
    monkeypatch: pytest.MonkeyPatch,
    interval: int,
) -> None:
    """Invalid intervals return a form error."""
    from unittest.mock import MagicMock

    from custom_components.ha_inspector.config_flow import (
        HAInspectorOptionsFlow,
    )
    from custom_components.ha_inspector.const import (
        CONF_PERIODIC_INSPECTION_ENABLED,
        CONF_PERIODIC_INSPECTION_INTERVAL,
        CONF_PERIODIC_INSPECTION_PROFILE,
    )

    entry = MagicMock()
    entry.options = {}

    flow = HAInspectorOptionsFlow()

    monkeypatch.setattr(
        type(flow),
        "config_entry",
        property(lambda self: entry),
    )

    monkeypatch.setattr(
        flow,
        "async_show_form",
        lambda **kwargs: kwargs,
    )

    result = await flow.async_step_init(
        {
            CONF_PERIODIC_INSPECTION_ENABLED: True,
            CONF_PERIODIC_INSPECTION_INTERVAL: interval,
            CONF_PERIODIC_INSPECTION_PROFILE: "quick",
        }
    )

    assert result["step_id"] == "init"
    assert result["errors"] == {"base": "invalid_options"}


async def test_options_flow_rejects_unknown_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unknown profiles return a form error."""
    from unittest.mock import MagicMock

    from custom_components.ha_inspector.config_flow import (
        HAInspectorOptionsFlow,
    )
    from custom_components.ha_inspector.const import (
        CONF_PERIODIC_INSPECTION_ENABLED,
        CONF_PERIODIC_INSPECTION_INTERVAL,
        CONF_PERIODIC_INSPECTION_PROFILE,
    )

    entry = MagicMock()
    entry.options = {}

    flow = HAInspectorOptionsFlow()

    monkeypatch.setattr(
        type(flow),
        "config_entry",
        property(lambda self: entry),
    )

    monkeypatch.setattr(
        flow,
        "async_show_form",
        lambda **kwargs: kwargs,
    )

    result = await flow.async_step_init(
        {
            CONF_PERIODIC_INSPECTION_ENABLED: True,
            CONF_PERIODIC_INSPECTION_INTERVAL: 60,
            CONF_PERIODIC_INSPECTION_PROFILE: "nonexistent_profile",
        }
    )

    assert result["step_id"] == "init"
    assert result["errors"] == {"base": "invalid_options"}
