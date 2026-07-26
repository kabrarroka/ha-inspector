"""Tests for HA Inspector service registration."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
import voluptuous as vol

from homeassistant.core import SupportsResponse
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from custom_components.ha_inspector.const import DOMAIN
from custom_components.ha_inspector.engine.inspection_service import (
    InspectionRequestError,
)
from custom_components.ha_inspector.service_adapter import (
    InspectionServiceAdapterError,
)
from custom_components.ha_inspector.services import (
    SERVICE_RUN_INSPECTION,
    SERVICE_RUN_INSPECTION_SCHEMA,
    async_register_services,
    async_unregister_services,
)


class FakeServiceRegistry:
    def __init__(self) -> None:
        self.handlers = {}
        self.registrations = []
        self.removals = []

    def has_service(self, domain, service) -> bool:
        return (domain, service) in self.handlers

    def async_register(
        self,
        domain,
        service,
        handler,
        *,
        schema=None,
        supports_response=None,
    ) -> None:
        self.handlers[(domain, service)] = handler
        self.registrations.append(
            {
                "domain": domain,
                "service": service,
                "handler": handler,
                "schema": schema,
                "supports_response": supports_response,
            }
        )

    def async_remove(self, domain, service) -> None:
        self.handlers.pop((domain, service), None)
        self.removals.append((domain, service))


def make_hass():
    return SimpleNamespace(services=FakeServiceRegistry())


def make_call(data=None):
    return SimpleNamespace(data=data or {})


def test_schema_accepts_all_supported_fields() -> None:
    validated = SERVICE_RUN_INSPECTION_SCHEMA(
        {
            "profile": "quick",
            "rule_ids": "system.core",
            "categories": ["system"],
            "tags": ["core"],
            "exclude_rule_ids": [],
            "exclude_categories": ["experimental"],
            "exclude_tags": ["slow"],
            "strict": False,
        }
    )

    assert validated["rule_ids"] == ["system.core"]
    assert validated["strict"] is False


def test_schema_rejects_unknown_fields() -> None:
    with pytest.raises(vol.Invalid):
        SERVICE_RUN_INSPECTION_SCHEMA(
            {"unsupported": True}
        )


def test_schema_defaults_strict_to_true() -> None:
    assert SERVICE_RUN_INSPECTION_SCHEMA({})["strict"] is True


def test_registers_response_only_service() -> None:
    hass = make_hass()
    adapter = SimpleNamespace(async_handle=AsyncMock())

    async_register_services(hass, adapter)

    registration = hass.services.registrations[0]
    assert registration["domain"] == DOMAIN
    assert registration["service"] == SERVICE_RUN_INSPECTION
    assert registration["schema"] is SERVICE_RUN_INSPECTION_SCHEMA
    assert (
        registration["supports_response"]
        is SupportsResponse.ONLY
    )


def test_registration_is_idempotent() -> None:
    hass = make_hass()
    adapter = SimpleNamespace(async_handle=AsyncMock())

    async_register_services(hass, adapter)
    async_register_services(hass, adapter)

    assert len(hass.services.registrations) == 1


@pytest.mark.asyncio
async def test_handler_delegates_to_adapter() -> None:
    hass = make_hass()
    adapter = SimpleNamespace(
        async_handle=AsyncMock(
            return_value={"checks_executed": 2}
        )
    )
    context = object()
    context_factory = Mock(return_value=context)
    call = make_call({"strict": False})

    async_register_services(
        hass,
        adapter,
        context_factory=context_factory,
    )
    handler = hass.services.handlers[
        (DOMAIN, SERVICE_RUN_INSPECTION)
    ]

    response = await handler(call)

    assert response == {"checks_executed": 2}
    context_factory.assert_called_once_with(hass, call)
    adapter.async_handle.assert_awaited_once_with(
        context,
        call.data,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [
        InspectionRequestError("invalid request"),
        InspectionServiceAdapterError("invalid data"),
        KeyError("unknown profile"),
    ],
)
async def test_domain_errors_become_validation_errors(
    error,
) -> None:
    hass = make_hass()
    adapter = SimpleNamespace(
        async_handle=AsyncMock(side_effect=error)
    )

    async_register_services(hass, adapter)
    handler = hass.services.handlers[
        (DOMAIN, SERVICE_RUN_INSPECTION)
    ]

    with pytest.raises(ServiceValidationError):
        await handler(make_call())


@pytest.mark.asyncio
async def test_home_assistant_errors_are_preserved() -> None:
    hass = make_hass()
    original = HomeAssistantError("known failure")
    adapter = SimpleNamespace(
        async_handle=AsyncMock(side_effect=original)
    )

    async_register_services(hass, adapter)
    handler = hass.services.handlers[
        (DOMAIN, SERVICE_RUN_INSPECTION)
    ]

    with pytest.raises(HomeAssistantError) as caught:
        await handler(make_call())

    assert caught.value is original


@pytest.mark.asyncio
async def test_unexpected_errors_become_home_assistant_errors() -> None:
    hass = make_hass()
    adapter = SimpleNamespace(
        async_handle=AsyncMock(
            side_effect=RuntimeError("boom")
        )
    )

    async_register_services(hass, adapter)
    handler = hass.services.handlers[
        (DOMAIN, SERVICE_RUN_INSPECTION)
    ]

    with pytest.raises(
        HomeAssistantError,
        match="could not complete",
    ):
        await handler(make_call())


def test_unregister_removes_registered_service() -> None:
    hass = make_hass()
    adapter = SimpleNamespace(async_handle=AsyncMock())
    async_register_services(hass, adapter)

    async_unregister_services(hass)

    assert hass.services.removals == [
        (DOMAIN, SERVICE_RUN_INSPECTION)
    ]
    assert not hass.services.has_service(
        DOMAIN,
        SERVICE_RUN_INSPECTION,
    )


def test_unregister_is_idempotent() -> None:
    hass = make_hass()

    async_unregister_services(hass)

    assert hass.services.removals == []
