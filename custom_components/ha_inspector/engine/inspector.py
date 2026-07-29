"""Inspection orchestrator for HA Inspector."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from .collectors.base import BaseCollector
from .context import InspectionContext
from .registry import InspectionRegistry
from .result import InspectionResult
from .rule_engine import RuleEngine
from .rule_selector import RuleExecutionPlan
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
        """Initialize the inspector."""
        self._collectors = list(collectors or [])
        self._rules = list(rules or [])
        self._rule_engine = RuleEngine(self._rules)

    @classmethod
    def from_registry(cls, registry: InspectionRegistry) -> "Inspector":
        """Create an inspector from a registry."""
        return cls(
            collectors=registry.collectors,
            rules=registry.rules,
        )

    async def run(
        self,
        hass: HomeAssistant,
        *,
        diagnostics: bool = False,
    ) -> InspectionResult:
        """Run all collectors and rules."""
        context = InspectionContext()

        for collector in self._collectors:
            await collector.collect(hass, context)

        plan = RuleExecutionPlan(
            tuple(
                rule.metadata.rule_id
                for rule in self._rules
            )
        )

        result = await self._rule_engine.execute(
            context,
            plan,
        )

        result.metadata["collectors_executed"] = len(self._collectors)
        result.metadata["rules_discovered"] = len(self._rules)
        result.metadata["diagnostics_included"] = diagnostics

        if diagnostics:
            result.metadata["rules"] = [
                rule.metadata.as_dict()
                for rule in sorted(
                    self._rules,
                    key=lambda item: item.metadata.rule_id,
                )
            ]
            result.metadata["context"] = self._diagnostic_context(context)

        return result

    @staticmethod
    def _diagnostic_context(
        context: InspectionContext,
    ) -> dict[str, object]:
        """Return a diagnostics-safe representation of the context."""
        sensitive_system_keys = {
            "latitude",
            "longitude",
            "internal_url",
            "external_url",
            "config_directory",
            "python_executable",
        }

        safe_system = {
            key: value
            for key, value in context.system.items()
            if key not in sensitive_system_keys
        }

        return {
            "system": safe_system,
            "storage": context.storage,
            "recorder": context.recorder,
            "integrations": context.integrations,
            "entities": context.entities,
        }


__all__ = ["Inspector"]
