"""Template and configuration reference inspection helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.helpers.template import Template, is_template_string

from .entity_references import ReferencePath, discover_entity_references


@dataclass(frozen=True, slots=True)
class TemplateReferences:
    """Represent dependencies discovered in one configuration string."""

    entities: tuple[str, ...]
    domains: tuple[str, ...]
    all_states: bool = False
    all_states_lifecycle: bool = False
    template: bool = False
    error: str | None = None


@dataclass(frozen=True, slots=True)
class ConfigurationReference:
    """Represent dependencies discovered at one configuration path."""

    path: ReferencePath
    entities: tuple[str, ...]
    domains: tuple[str, ...]
    all_states: bool = False
    all_states_lifecycle: bool = False
    template: bool = False
    error: str | None = None


def inspect_template_references(
    hass: HomeAssistant,
    value: str,
) -> TemplateReferences:
    """Inspect entity and domain references in one configuration string."""
    if not is_template_string(value):
        entities = {
            reference.entity_id
            for reference in discover_entity_references(value)
        }

        return TemplateReferences(
            entities=tuple(sorted(entities)),
            domains=(),
            template=False,
        )

    render_info = Template(value, hass).async_render_to_info()

    domains = set(render_info.domains)
    domains.update(render_info.domains_lifecycle)

    return TemplateReferences(
        entities=tuple(sorted(render_info.entities)),
        domains=tuple(sorted(domains)),
        all_states=render_info.all_states,
        all_states_lifecycle=render_info.all_states_lifecycle,
        template=True,
        error=(
            str(render_info.exception)
            if render_info.exception is not None
            else None
        ),
    )


def inspect_configuration_references(
    hass: HomeAssistant,
    value: object,
) -> list[ConfigurationReference]:
    """Inspect references in a nested configuration value."""
    references: list[ConfigurationReference] = []

    def visit(current: object, path: ReferencePath) -> None:
        if isinstance(current, str):
            discovered = inspect_template_references(hass, current)

            if (
                discovered.entities
                or discovered.domains
                or discovered.all_states
                or discovered.all_states_lifecycle
                or discovered.error is not None
            ):
                references.append(
                    ConfigurationReference(
                        path=path,
                        entities=discovered.entities,
                        domains=discovered.domains,
                        all_states=discovered.all_states,
                        all_states_lifecycle=discovered.all_states_lifecycle,
                        template=discovered.template,
                        error=discovered.error,
                    )
                )
            return

        if isinstance(current, Mapping):
            for key, nested_value in current.items():
                visit(nested_value, (*path, str(key)))
            return

        if isinstance(current, Sequence) and not isinstance(
            current,
            (str, bytes, bytearray),
        ):
            for index, nested_value in enumerate(current):
                visit(nested_value, (*path, index))

    visit(value, ())
    return references
