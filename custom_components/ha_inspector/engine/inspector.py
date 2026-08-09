"""Inspection orchestrator for HA Inspector."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from .collectors.base import BaseCollector
from .context import InspectionContext
from .registry import InspectionRegistry
from .request import InspectionRequest
from .result import InspectionResult
from .rule_engine import RuleEngine
from .rule_registry import RuleRegistry
from .rule_selector import RuleSelector
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

        self._rule_registry = RuleRegistry(self._rules)
        self._rule_selector = RuleSelector(self._rule_registry)
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
        request: InspectionRequest | None = None,
        diagnostics: bool | None = None,
    ) -> InspectionResult:
        """Run collectors and the rules selected by the request."""
        if request is None:
            request = InspectionRequest()

        if diagnostics is not None:
            request_data = request.as_dict()
            request_data["diagnostics"] = diagnostics
            request = InspectionRequest.from_dict(request_data)

        context = InspectionContext()

        for collector in self._collectors:
            await collector.collect(hass, context)

        plan = self._rule_selector.select(
            **request.selector_options(),
        )

        result = await self._rule_engine.execute(
            context,
            plan,
        )

        result.metadata["collectors_executed"] = len(self._collectors)
        result.metadata["rules_discovered"] = len(self._rules)
        result.metadata["rules_selected"] = len(plan)
        result.metadata["execution_plan"] = plan.as_dict()
        result.metadata["request"] = request.as_dict()
        result.metadata["diagnostics_included"] = request.diagnostics

        if request.diagnostics:
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
            for key, value in context.system.as_dict().items()
            if key not in sensitive_system_keys
        }

        return {
            "system": safe_system,
            "storage": context.storage.as_dict(),
            "backups": context.backups.as_dict(),
            "recorder": context.recorder.as_dict(),
            "integrations": context.integrations.as_dict(),
            "entities": context.entities.as_dict(),
        }


__all__ = ["Inspector"]
