"""Inspection orchestrator for HA Inspector."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from time import perf_counter
from typing import TYPE_CHECKING

from .collectors.base import BaseCollector
from .context import InspectionContext
from .dependency_diagnostics import dependency_diagnostics
from .i18n import normalize_language
from .registry import InspectionRegistry
from .remediation_workflow_diagnostics import (
    remediation_workflow_diagnostics,
)
from .request import InspectionRequest
from .result import InspectionResult
from .rule_engine import RuleEngine
from .rule_registry import RuleRegistry
from .rule_selector import RuleSelector
from .rules.base import BaseRule
from .suppression import FindingSuppressionPolicy

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


_LOGGER = logging.getLogger(__name__)


class Inspector:
    """Coordinate collectors and inspection rules."""

    def __init__(
        self,
        collectors: Sequence[BaseCollector] | None = None,
        rules: Sequence[BaseRule] | None = None,
        clock: Callable[[], float] = perf_counter,
    ) -> None:
        """Initialize the inspector."""
        self._collectors = list(collectors or [])
        self._rules = list(rules or [])
        self._clock = clock

        self._rule_registry = RuleRegistry(self._rules)
        self._rule_selector = RuleSelector(self._rule_registry)
        self._rule_engine = RuleEngine(self._rules)

    @classmethod
    def from_registry(cls, registry: InspectionRegistry) -> Inspector:
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
        suppression: FindingSuppressionPolicy | None = None,
    ) -> InspectionResult:
        """Run collectors and the rules selected by the request."""
        if request is None:
            request = InspectionRequest()

        if diagnostics is not None:
            request_data = request.as_dict()
            request_data["diagnostics"] = diagnostics
            request = InspectionRequest.from_dict(request_data)

        requested_language = request.language

        if requested_language is None:
            requested_language = getattr(
                getattr(hass, "config", None),
                "language",
                None,
            )

        language = normalize_language(requested_language)
        context = InspectionContext(language=language)

        inspection_started = self._clock()
        collector_timings: dict[str, float] = {}
        collector_errors: list[dict[str, str]] = []

        collectors_started = self._clock()
        for collector in self._collectors:
            collector_started = self._clock()
            try:
                await collector.collect(hass, context)
            except Exception as err:
                _LOGGER.exception(
                    "Collector %s failed during inspection",
                    collector.collector_id,
                )
                collector_errors.append(
                    {
                        "collector_id": collector.collector_id,
                        "error_type": type(err).__name__,
                        "message": str(err),
                    }
                )
            finally:
                collector_timings[collector.collector_id] = (
                    self._clock() - collector_started
                )
        collectors_seconds = self._clock() - collectors_started

        plan = self._rule_selector.select(
            **request.selector_options(),
        )

        rules_started = self._clock()
        result = await self._rule_engine.execute(
            context,
            plan,
            suppression=suppression,
        )
        rules_seconds = self._clock() - rules_started
        inspection_seconds = self._clock() - inspection_started

        result.dependency_diagnostics = dependency_diagnostics(
            context.entities
        )
        result.remediation_workflow_diagnostics = (
            remediation_workflow_diagnostics(context.entities)
        )

        result.metadata["timings"] = {
            "inspection_seconds": inspection_seconds,
            "collectors_seconds": collectors_seconds,
            "rules_seconds": rules_seconds,
            "collectors": collector_timings,
        }
        result.metadata["collectors_executed"] = len(self._collectors)
        result.metadata["collectors_failed"] = len(collector_errors)
        result.metadata["collectors_succeeded"] = (
            len(self._collectors) - len(collector_errors)
        )
        result.metadata["collector_errors"] = collector_errors
        result.metadata["rules_discovered"] = len(self._rules)
        result.metadata["rules_selected"] = len(plan)
        result.metadata["execution_plan"] = plan.as_dict()
        result.metadata["language"] = language
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
            "logs": context.logs.as_dict(),
            "addons": context.addons.as_dict(),
            "repairs": context.repairs.as_dict(),
            "backups": context.backups.as_dict(),
            "recorder": context.recorder.as_dict(),
            "integrations": context.integrations.as_dict(),
            "entities": context.entities.as_dict(),
        }


__all__ = ["Inspector"]
