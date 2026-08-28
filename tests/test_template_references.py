"""Tests for template reference inspection helpers."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant

from custom_components.ha_inspector.engine.template_references import (
    inspect_configuration_references,
    inspect_template_references,
)


@pytest.fixture
async def hass() -> HomeAssistant:
    """Create a minimal Home Assistant instance for template tests."""
    instance = HomeAssistant("/tmp/ha-inspector-template-tests")
    yield instance
    await instance.async_stop()


@pytest.mark.asyncio
async def test_static_configuration_reference(
    hass: HomeAssistant,
) -> None:
    """Static configuration strings expose literal entity references."""
    references = inspect_template_references(
        hass,
        "sensor.temperature",
    )

    assert references.entities == ("sensor.temperature",)
    assert references.domains == ()
    assert references.all_states is False
    assert references.all_states_lifecycle is False
    assert references.template is False


@pytest.mark.asyncio
async def test_template_entity_reference(
    hass: HomeAssistant,
) -> None:
    """Templates expose concrete entity dependencies."""
    hass.states.async_set("sensor.temperature", "21")

    references = inspect_template_references(
        hass,
        "{{ states('sensor.temperature') }}",
    )

    assert references.entities == ("sensor.temperature",)
    assert references.domains == ()
    assert references.template is True


@pytest.mark.asyncio
async def test_template_multiple_entity_references(
    hass: HomeAssistant,
) -> None:
    """Templates expose multiple unique entity dependencies."""
    hass.states.async_set("sensor.temperature", "21")
    hass.states.async_set("binary_sensor.window", "off")

    references = inspect_template_references(
        hass,
        "{{ states('sensor.temperature') }} "
        "{{ is_state('binary_sensor.window', 'on') }}",
    )

    assert references.entities == (
        "binary_sensor.window",
        "sensor.temperature",
    )
    assert references.domains == ()


@pytest.mark.asyncio
async def test_template_dynamic_entity_reference(
    hass: HomeAssistant,
) -> None:
    """Home Assistant resolves simple dynamic entity references."""
    hass.states.async_set("sensor.temperature", "21")

    references = inspect_template_references(
        hass,
        "{% set entity = 'sensor.temperature' %}"
        "{{ states(entity) }}",
    )

    assert references.entities == ("sensor.temperature",)
    assert references.domains == ()


@pytest.mark.asyncio
async def test_template_domain_reference(
    hass: HomeAssistant,
) -> None:
    """Domain-wide template access is represented as a domain dependency."""
    hass.states.async_set("sensor.temperature", "21")

    references = inspect_template_references(
        hass,
        "{{ states.sensor | list | count }}",
    )

    assert references.entities == ()
    assert references.domains == ("sensor",)
    assert references.all_states is False
    assert references.all_states_lifecycle is False
    assert references.template is True


@pytest.mark.asyncio
async def test_template_explicit_and_runtime_references_are_deduplicated(
    hass: HomeAssistant,
) -> None:
    """Literal and runtime discovery should not duplicate an entity."""
    hass.states.async_set("sensor.temperature", "21")

    references = inspect_template_references(
        hass,
        "{{ states('sensor.temperature') }}",
    )

    assert references.entities == ("sensor.temperature",)


@pytest.mark.asyncio
async def test_nested_configuration_references(
    hass: HomeAssistant,
) -> None:
    """Nested configuration references retain their source paths."""
    hass.states.async_set("sensor.temperature", "21")
    hass.states.async_set("binary_sensor.window", "off")

    configuration = {
        "trigger": {
            "entity_id": "binary_sensor.window",
        },
        "actions": [
            {
                "target": {
                    "entity_id": "light.kitchen",
                }
            },
            {
                "value_template": "{{ states('sensor.temperature') }}",
            },
        ],
    }

    references = inspect_configuration_references(hass, configuration)

    assert [(reference.path, reference.entities) for reference in references] == [
        (
            ("trigger", "entity_id"),
            ("binary_sensor.window",),
        ),
        (
            ("actions", 0, "target", "entity_id"),
            ("light.kitchen",),
        ),
        (
            ("actions", 1, "value_template"),
            ("sensor.temperature",),
        ),
    ]

    assert references[0].template is False
    assert references[1].template is False
    assert references[2].template is True


@pytest.mark.asyncio
async def test_nested_configuration_domain_reference(
    hass: HomeAssistant,
) -> None:
    """Domain dependencies retain their configuration path."""
    hass.states.async_set("sensor.temperature", "21")

    references = inspect_configuration_references(
        hass,
        {
            "condition": {
                "value_template": "{{ states.sensor | list | count }}",
            }
        },
    )

    assert len(references) == 1
    assert references[0].path == ("condition", "value_template")
    assert references[0].entities == ()
    assert references[0].domains == ("sensor",)
    assert references[0].template is True


@pytest.mark.asyncio
async def test_nested_configuration_ignores_values_without_references(
    hass: HomeAssistant,
) -> None:
    """Configuration values without dependencies are ignored."""
    references = inspect_configuration_references(
        hass,
        {
            "alias": "Example automation",
            "enabled": True,
            "mode": "single",
            "count": 3,
            "items": [None, False, "plain text"],
        },
    )

    assert references == []


@pytest.mark.asyncio
async def test_template_all_states_reference(
    hass: HomeAssistant,
) -> None:
    """Global state access exposes lifecycle-sensitive dependencies."""
    hass.states.async_set("sensor.temperature", "21")

    references = inspect_template_references(
        hass,
        "{{ states | list | count }}",
    )

    assert references.entities == ()
    assert references.domains == ()
    assert references.all_states is True
    assert references.all_states_lifecycle is True
    assert references.template is True
    assert references.error is None


@pytest.mark.asyncio
async def test_template_all_states_iteration(
    hass: HomeAssistant,
) -> None:
    """State iteration can depend on all states without lifecycle tracking."""
    hass.states.async_set("sensor.temperature", "21")

    references = inspect_template_references(
        hass,
        "{% for state in states %}"
        "{{ state.entity_id }}"
        "{% endfor %}",
    )

    assert references.entities == ()
    assert references.domains == ()
    assert references.all_states is True
    assert references.all_states_lifecycle is False
    assert references.error is None


@pytest.mark.asyncio
async def test_template_mixed_domain_and_entity_references(
    hass: HomeAssistant,
) -> None:
    """Templates may expose entity and domain dependencies together."""
    hass.states.async_set("sensor.temperature", "21")

    references = inspect_template_references(
        hass,
        "{{ states.sensor | list | count }} "
        "{{ states('light.kitchen') }}",
    )

    assert references.entities == ("light.kitchen",)
    assert references.domains == ("sensor",)
    assert references.all_states is False
    assert references.all_states_lifecycle is False
    assert references.error is None


@pytest.mark.asyncio
async def test_template_render_error_is_reported(
    hass: HomeAssistant,
) -> None:
    """Unresolvable templates retain their inspection error."""
    references = inspect_template_references(
        hass,
        "{{ states(entity_id) }}",
    )

    assert references.entities == ()
    assert references.domains == ()
    assert references.template is True
    assert references.error is not None
    assert "'entity_id' is undefined" in references.error


@pytest.mark.asyncio
async def test_invalid_template_is_reported_in_configuration(
    hass: HomeAssistant,
) -> None:
    """Invalid templates remain visible during configuration inspection."""
    references = inspect_configuration_references(
        hass,
        {
            "condition": {
                "value_template": "{{ states('sensor.temperature') ",
            }
        },
    )

    assert len(references) == 1
    assert references[0].path == ("condition", "value_template")
    assert references[0].entities == ()
    assert references[0].domains == ()
    assert references[0].template is True
    assert references[0].error is not None
    assert "TemplateSyntaxError" in references[0].error
