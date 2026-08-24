"""Tests for exportable diagnostic reports."""

from __future__ import annotations

from custom_components.ha_inspector.engine.diagnostic_report import (
    DIAGNOSTIC_REPORT_SCHEMA_VERSION,
    DiagnosticReport,
    build_diagnostic_report,
)


def sample_result() -> dict:
    """Return a representative serialized inspection result."""
    return {
        "schema_version": 2,
        "started_at": "2026-08-24T08:00:00+00:00",
        "finished_at": "2026-08-24T08:00:01+00:00",
        "duration_seconds": 1.0,
        "checks_executed": 3,
        "total_findings": 1,
        "score": 95,
        "health": {
            "score": 95,
            "status": "excellent",
        },
        "summary": {
            "critical": 0,
            "error": 0,
            "warning": 1,
            "info": 0,
        },
        "health_summary": {
            "excellent": 2,
        },
        "domain_health": {
            "system": {
                "score": 100,
            },
        },
        "dashboard_summary": {
            "status": "excellent",
            "score": 95,
        },
        "findings": [
            {
                "finding_id": "TEST_WARNING",
                "severity": "warning",
                "message": "Test warning",
            }
        ],
        "metadata": {
            "profile": "full",
            "language": "es",
            "diagnostics_included": True,
            "collectors_executed": 3,
            "collectors_succeeded": 2,
            "collectors_failed": 1,
            "collector_errors": [
                {
                    "collector_id": "test",
                    "error_type": "RuntimeError",
                    "message": "failed",
                }
            ],
            "rules_discovered": 10,
            "rules_selected": 3,
            "timings": {
                "inspection_seconds": 1.0,
                "collectors_seconds": 0.5,
                "rules_seconds": 0.4,
            },
            "registry": {
                "collectors": ["system"],
                "rules": ["TEST_WARNING"],
            },
            "execution_plan": {
                "rule_ids": ["TEST_WARNING"],
            },
            "request": {
                "diagnostics": True,
            },
            "suppressed_findings_count": 2,
            "context": {
                "system": {
                    "secret": "must not be exported",
                }
            },
            "unexpected": "must not be exported",
        },
    }


def test_diagnostic_report_schema_version() -> None:
    """Diagnostic report schema starts at version one."""
    assert DIAGNOSTIC_REPORT_SCHEMA_VERSION == 1


def test_diagnostic_report_contains_stable_sections() -> None:
    """Report exposes stable top-level diagnostic sections."""
    report = DiagnosticReport(
        version="1.0.0",
        result=sample_result(),
    ).as_dict()

    assert set(report) == {
        "schema_version",
        "generator",
        "inspection",
        "findings",
        "operational",
    }

    assert report["schema_version"] == 1
    assert report["generator"] == {
        "name": "HA Inspector",
        "version": "1.0.0",
    }


def test_diagnostic_report_contains_inspection_summary() -> None:
    """Report contains the useful inspection summary."""
    report = build_diagnostic_report(
        version="1.0.0",
        result=sample_result(),
    )

    inspection = report["inspection"]

    assert inspection["schema_version"] == 2
    assert inspection["checks_executed"] == 3
    assert inspection["total_findings"] == 1
    assert inspection["score"] == 95
    assert inspection["dashboard_summary"]["status"] == "excellent"


def test_diagnostic_report_contains_findings() -> None:
    """Report exports inspection findings."""
    report = build_diagnostic_report(
        version="1.0.0",
        result=sample_result(),
    )

    assert report["findings"] == [
        {
            "finding_id": "TEST_WARNING",
            "severity": "warning",
            "message": "Test warning",
        }
    ]


def test_diagnostic_report_contains_operational_diagnostics() -> None:
    """Report exposes operational diagnostic information."""
    report = build_diagnostic_report(
        version="1.0.0",
        result=sample_result(),
    )

    operational = report["operational"]

    assert operational["collectors_executed"] == 3
    assert operational["collectors_succeeded"] == 2
    assert operational["collectors_failed"] == 1
    assert operational["collector_errors"][0]["collector_id"] == "test"
    assert operational["timings"]["inspection_seconds"] == 1.0
    assert operational["suppressed_findings_count"] == 2


def test_diagnostic_report_does_not_export_context() -> None:
    """Raw diagnostic context is deliberately excluded from exports."""
    report = build_diagnostic_report(
        version="1.0.0",
        result=sample_result(),
    )

    assert "context" not in report["operational"]
    assert "unexpected" not in report["operational"]


def test_diagnostic_report_handles_missing_optional_data() -> None:
    """Minimal historical results can still produce a report."""
    report = build_diagnostic_report(
        version="1.0.0",
        result={},
    )

    assert report["inspection"]["checks_executed"] == 0
    assert report["inspection"]["total_findings"] == 0
    assert report["findings"] == []
    assert report["operational"] == {}


def test_diagnostic_report_does_not_mutate_source() -> None:
    """Report construction does not retain mutable source references."""
    source = sample_result()

    report = build_diagnostic_report(
        version="1.0.0",
        result=source,
    )

    report["findings"][0]["message"] = "changed"
    report["operational"]["collector_errors"][0]["message"] = "changed"

    assert source["findings"][0]["message"] == "Test warning"
    assert (
        source["metadata"]["collector_errors"][0]["message"]
        == "failed"
    )
