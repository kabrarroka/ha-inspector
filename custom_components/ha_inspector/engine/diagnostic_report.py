"""Exportable diagnostic report for HA Inspector."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

DIAGNOSTIC_REPORT_SCHEMA_VERSION = 1


class DiagnosticReport:
    """Build a stable exportable report from an inspection result."""

    def __init__(
        self,
        *,
        version: str,
        result: Mapping[str, Any],
    ) -> None:
        """Initialize the diagnostic report."""
        self._version = version
        self._result = deepcopy(dict(result))

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-safe exportable diagnostic report."""
        result = self._result

        return {
            "schema_version": DIAGNOSTIC_REPORT_SCHEMA_VERSION,
            "generator": {
                "name": "HA Inspector",
                "version": self._version,
            },
            "inspection": {
                "schema_version": result.get("schema_version"),
                "started_at": result.get("started_at"),
                "finished_at": result.get("finished_at"),
                "duration_seconds": result.get("duration_seconds"),
                "checks_executed": result.get("checks_executed", 0),
                "total_findings": result.get("total_findings", 0),
                "score": result.get("score"),
                "health": deepcopy(result.get("health")),
                "summary": deepcopy(result.get("summary", {})),
                "health_summary": deepcopy(
                    result.get("health_summary", {})
                ),
                "domain_health": deepcopy(
                    result.get("domain_health", {})
                ),
                "dashboard_summary": deepcopy(
                    result.get("dashboard_summary", {})
                ),
            },
            "findings": deepcopy(result.get("findings", [])),
            "operational": self._operational_metadata(
                result.get("metadata")
            ),
        }

    @staticmethod
    def _operational_metadata(
        metadata: object,
    ) -> dict[str, Any]:
        """Return diagnostic-safe operational metadata."""
        if not isinstance(metadata, Mapping):
            return {}

        allowed_keys = (
            "profile",
            "language",
            "diagnostics_included",
            "collectors_executed",
            "collectors_succeeded",
            "collectors_failed",
            "collector_errors",
            "rules_discovered",
            "rules_selected",
            "timings",
            "registry",
            "execution_plan",
            "request",
            "suppressed_findings_count",
        )

        return {
            key: deepcopy(metadata[key])
            for key in allowed_keys
            if key in metadata
        }


def build_diagnostic_report(
    *,
    version: str,
    result: Mapping[str, Any],
) -> dict[str, Any]:
    """Build an exportable diagnostic report."""
    return DiagnosticReport(
        version=version,
        result=result,
    ).as_dict()


__all__ = [
    "DIAGNOSTIC_REPORT_SCHEMA_VERSION",
    "DiagnosticReport",
    "build_diagnostic_report",
]
