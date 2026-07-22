"""Inspection orchestrator for HA Inspector."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from .collectors.base import BaseCollector
from .context import InspectionContext
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

    async def run(self, hass: HomeAssistant) -> InspectionResult:
        """Run all collectors and rules."""
        context = InspectionContext()
        result = InspectionResult()

        for collector in self._collectors:
            await collector.collect(hass, context)

        for rule in self._rules:
            findings = await rule.check(context)
            result.add_many(findings)
            result.checks_executed += 1

        result.metadata["collectors_executed"] = len(self._collectors)
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

        result.metadata["context"] = {
            "system": safe_system,
            "recorder": context.recorder,
            "integrations": context.integrations,
            "entities": context.entities,
        }
        result.finish()

        return result