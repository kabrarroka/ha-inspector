"""Inspection orchestrator for HA Inspector."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from .collectors.base import BaseCollector
from .context import InspectionContext
from .registry import InspectionRegistry
from .result import InspectionResult
from .rules.base import BaseRule

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class Inspector:
    """Coordinate collectors and inspection rules."""

    def __init__(
        self,
        collectors: Sequence[BaseCollector] | None = None,
        rules: Sequence[BaseRule] | None = None,
    ) -> None:
        self._collectors = list(collectors or [])
        self._rules = list(rules or [])

    @classmethod
    def from_registry(cls, registry: InspectionRegistry) -> "Inspector":
        """Create an inspector from a registry."""
        return cls(collectors=registry.collectors, rules=registry.rules)

    async def run(
        self,
        hass: HomeAssistant,
        *,
        diagnostics: bool = False,
    ) -> InspectionResult:
        """Run all collectors and rules."""
        context = InspectionContext()
        result = InspectionResult()

        for collector in self._collectors:
            await collector.collect(hass, context)

        rule_catalog: list[dict[str, object]] = []
        for rule in self._rules:
            descriptor = rule.metadata
            findings = await rule.check(context)
            result.record_rule(
                category=descriptor.category,
                weight=descriptor.weight,
                findings=findings,
            )
            rule_catalog.append(descriptor.as_dict())

        result.metadata["collectors_executed"] = len(self._collectors)
        result.metadata["rules_discovered"] = len(self._rules)
        result.metadata["diagnostics_included"] = diagnostics

        if diagnostics:
            safe_system = {
                key: value
                for key, value in context.system.items()
                if key not in {
                    "latitude",
                    "longitude",
                    "internal_url",
                    "external_url",
                    "config_directory",
                    "python_executable",
                }
            }
            result.metadata["rules"] = rule_catalog
            result.metadata["context"] = {
                "system": safe_system,
                "storage": context.storage,
                "recorder": context.recorder,
                "integrations": context.integrations,
                "entities": context.entities,
            }

        result.finish()
        return result
