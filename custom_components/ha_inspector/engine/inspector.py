"""Inspection orchestrator for HA Inspector."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from .collectors.base import BaseCollector
from .context import InspectionContext
from .registry import InspectionRegistry
from .result import InspectionResult
from .rule_engine import RuleEngine
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
        self._rule_engine = RuleEngine(self._rules)

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
        execution_errors: list[dict[str, str]] = []

        collectors_executed = 0
        for collector in self._collectors:
            try:
                await collector.collect(hass, context)
            except Exception as err:  # noqa: BLE001 - component isolation
                execution_errors.append(
                    {
                        "type": "collector",
                        "id": collector.collector_id,
                        "error": type(err).__name__,
                        "message": str(err),
                    }
                )
            else:
                collectors_executed += 1

        rule_executions = await self._rule_engine.run(context)
        rule_catalog: list[dict[str, object]] = []
        rules_executed = 0

        for rule, execution in zip(
            self._rules,
            rule_executions,
            strict=True,
        ):
            descriptor = rule.metadata
            rule_catalog.append(descriptor.as_dict())

            if execution.success:
                result.record_rule(
                    category=descriptor.category,
                    weight=descriptor.weight,
                    findings=execution.findings,
                )
                rules_executed += 1
                continue

            error_name, error_message = self._split_execution_error(
                execution.error
            )
            execution_errors.append(
                {
                    "type": "rule",
                    "id": descriptor.rule_id,
                    "error": error_name,
                    "message": error_message,
                }
            )

        result.findings.sort(
            key=lambda finding: (
                -int(finding.severity),
                finding.finding_id,
            )
        )

        result.metadata["collectors_executed"] = collectors_executed
        result.metadata["rules_discovered"] = len(self._rules)
        result.metadata["rules_executed"] = rules_executed
        result.metadata["diagnostics_included"] = diagnostics

        if execution_errors:
            result.metadata["execution_errors"] = execution_errors

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

    @staticmethod
    def _split_execution_error(
        error: str | None,
    ) -> tuple[str, str]:
        """Split the internal engine error into public error fields."""
        if not error:
            return "UnknownError", ""

        error_name, separator, message = error.partition(": ")
        if not separator:
            return error_name, ""

        return error_name, message
