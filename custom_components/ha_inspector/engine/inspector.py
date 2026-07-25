"""Inspection orchestrator for HA Inspector."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from .collectors.base import BaseCollector
from .context import InspectionContext
from .registry import InspectionRegistry
from .result import InspectionResult
from .rules.base import BaseRule

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


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
        """Run all collectors and rules without aborting on one failure."""
        context = InspectionContext()
        result = InspectionResult()
        execution_errors: list[dict[str, str]] = []

        for collector in self._collectors:
            try:
                await collector.collect(hass, context)
            except Exception as err:  # noqa: BLE001
                collector_id = getattr(
                    collector,
                    "collector_id",
                    collector.__class__.__name__,
                )
                _LOGGER.exception("Collector %s failed", collector_id)
                execution_errors.append(
                    self._error_details("collector", collector_id, err)
                )

        rule_catalog: list[dict[str, Any]] = []
        for rule in self._rules:
            descriptor = rule.metadata
            rule_catalog.append(descriptor.as_dict())

            try:
                findings = await rule.check(context)
            except Exception as err:  # noqa: BLE001
                rule_id = getattr(
                    descriptor,
                    "rule_id",
                    getattr(descriptor, "id", rule.__class__.__name__),
                )
                _LOGGER.exception("Rule %s failed", rule_id)
                execution_errors.append(
                    self._error_details("rule", rule_id, err)
                )
                continue

            result.record_rule(
                category=descriptor.category,
                weight=descriptor.weight,
                findings=findings,
            )

        result.findings.sort(
            key=lambda finding: (-int(finding.severity), finding.finding_id)
        )
        result.metadata["collectors_executed"] = len(self._collectors)
        result.metadata["rules_discovered"] = len(self._rules)
        result.metadata["rules_executed"] = result.checks_executed
        result.metadata["diagnostics_included"] = diagnostics

        if execution_errors:
            result.metadata["execution_errors"] = execution_errors

        if diagnostics:
            safe_system = {
                key: value
                for key, value in context.system.items()
                if key
                not in {
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

    @staticmethod
    def _error_details(
        component_type: str,
        component_id: str,
        err: Exception,
    ) -> dict[str, str]:
        """Return safe, serializable details for an execution error."""
        return {
            "type": component_type,
            "id": component_id,
            "error": err.__class__.__name__,
            "message": str(err),
        }
