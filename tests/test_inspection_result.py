"""Tests for the HA Inspector inspection result and health score."""

from datetime import UTC, datetime, timedelta

from custom_components.ha_inspector.engine.models import Finding
from custom_components.ha_inspector.engine.result import InspectionResult
from custom_components.ha_inspector.engine.severity import Severity


def _finding(finding_id: str, severity: Severity) -> Finding:
    return Finding(
        finding_id=finding_id,
        severity=severity,
        title=f"Finding {finding_id}",
        description="Test finding",
    )


def test_empty_result_has_perfect_score() -> None:
    result = InspectionResult()

    assert result.score == 100
    assert result.total_findings == 0
    assert result.categories == {}


def test_record_rule_updates_score_and_category_summary() -> None:
    result = InspectionResult()

    result.record_rule(
        category="entities",
        weight=20,
        findings=[
            _finding("entities.warning", Severity.WARNING),
            _finding("entities.error", Severity.ERROR),
        ],
    )

    # 20 * 0.30 + 20 * 0.70 = 20 penalty points.
    assert result.score == 80
    assert result.checks_executed == 1
    assert result.total_findings == 2
    assert result.categories == {
        "entities": {
            "health": {
                "score": 80,
                "max_score": 100,
                "status": "good",
                "penalty": 20.0,
            },
            "checks": 1,
            "findings": 2,
        }
    }


def test_score_never_drops_below_zero() -> None:
    result = InspectionResult()

    result.record_rule(
        category="system",
        weight=250,
        findings=[_finding("system.critical", Severity.CRITICAL)],
    )

    assert result.score == 0
    assert result.categories["system"]["health"]["score"] == 0


def test_negative_rule_weight_does_not_add_penalty() -> None:
    result = InspectionResult()

    result.record_rule(
        category="system",
        weight=-10,
        findings=[_finding("system.error", Severity.ERROR)],
    )

    assert result.score == 100


def test_duration_is_none_until_finished() -> None:
    result = InspectionResult()

    assert result.duration_seconds is None


def test_duration_uses_started_and_finished_times() -> None:
    started_at = datetime(2026, 7, 24, 8, 0, tzinfo=UTC)
    result = InspectionResult(
        started_at=started_at,
        finished_at=started_at + timedelta(seconds=1.25),
    )

    assert result.duration_seconds == 1.25


def test_as_dict_is_json_serializable_shape() -> None:
    started_at = datetime(2026, 7, 24, 8, 0, tzinfo=UTC)
    result = InspectionResult(started_at=started_at)
    result.record_rule(
        category="recorder",
        weight=10,
        findings=[_finding("recorder.warning", Severity.WARNING)],
    )

    payload = result.as_dict()

    assert payload["schema_version"] == 2
    assert payload["started_at"] == started_at.isoformat()
    assert payload["finished_at"] is None
    assert payload["score"] == 97
    assert payload["health"] == {
        "score": 97,
        "max_score": 100,
        "status": "excellent",
        "penalty": 3.0,
    }
    assert payload["summary"][Severity.WARNING.label] == 1
    assert payload["findings"][0]["id"] == "recorder.warning"

def test_health_summary_counts_categories_by_status() -> None:
    result = InspectionResult()

    result.record_rule(
        category="entities",
        weight=20,
        findings=[
            _finding("entities.warning", Severity.WARNING),
            _finding("entities.error", Severity.ERROR),
        ],
    )
    result.record_rule(
        category="storage",
        weight=10,
        findings=[
            _finding("storage.warning", Severity.WARNING),
        ],
    )
    result.record_rule(
        category="system",
        weight=100,
        findings=[
            _finding("system.critical", Severity.CRITICAL),
        ],
    )

    assert result.health_summary == {
        "excellent": 1,
        "good": 1,
        "fair": 0,
        "poor": 0,
        "critical": 1,
    }

def test_finish_sets_finished_at_and_duration() -> None:
    started_at = datetime.now(UTC) - timedelta(seconds=1)
    result = InspectionResult(started_at=started_at)

    result.finish()

    assert result.finished_at is not None
    assert result.finished_at >= started_at
    assert result.duration_seconds is not None
    assert result.duration_seconds >= 1

def test_health_status_returns_analytics_status() -> None:
    result = InspectionResult()

    result.record_rule(
        category="entities",
        weight=20,
        findings=[
            _finding("entities.warning", Severity.WARNING),
            _finding("entities.error", Severity.ERROR),
        ],
    )

    assert result.health_status.value == "good"

def test_presentation_groups_and_orders_findings() -> None:
    """Presentation groups categories and orders findings by severity."""
    result = InspectionResult()

    result.record_rule(
        category="system",
        weight=20,
        findings=[
            _finding("system.warning", Severity.WARNING),
            _finding("system.critical", Severity.CRITICAL),
            _finding("system.error", Severity.ERROR),
        ],
    )
    result.record_rule(
        category="entities",
        weight=10,
        findings=[
            _finding("entities.info", Severity.INFO),
            _finding("entities.warning", Severity.WARNING),
        ],
    )

    presentation = result.presentation

    assert [
        group["category"]
        for group in presentation
    ] == ["entities", "system"]

    assert [
        finding["id"]
        for finding in presentation[0]["findings"]
    ] == [
        "entities.warning",
        "entities.info",
    ]

    assert [
        finding["id"]
        for finding in presentation[1]["findings"]
    ] == [
        "system.critical",
        "system.error",
        "system.warning",
    ]


def test_presentation_includes_category_summary() -> None:
    """Presentation includes category health and counters."""
    result = InspectionResult()

    result.record_rule(
        category="storage",
        weight=10,
        findings=[
            _finding("storage.warning", Severity.WARNING),
        ],
    )

    group = result.presentation[0]

    assert group["category"] == "storage"
    assert group["checks"] == 1
    assert group["findings_count"] == 1
    assert group["health"] == result.categories["storage"]["health"]


def test_presentation_includes_empty_checked_category() -> None:
    """Checked categories without findings remain visible."""
    result = InspectionResult()

    result.record_rule(
        category="system",
        weight=20,
        findings=[],
    )

    assert result.presentation == [
        {
            "category": "system",
            "health": result.categories["system"]["health"],
            "checks": 1,
            "findings_count": 0,
            "findings": [],
        }
    ]


def test_as_dict_includes_presentation() -> None:
    """Serialized results expose presentation groups."""
    result = InspectionResult()

    result.record_rule(
        category="entities",
        weight=10,
        findings=[
            _finding("entities.warning", Severity.WARNING),
        ],
    )

    payload = result.as_dict()

    assert payload["presentation"] == result.presentation


def test_result_exposes_domain_health() -> None:
    """InspectionResult exposes primary domain health summaries."""
    result = InspectionResult()

    result.record_rule(
        category="entities",
        weight=20,
        findings=[
            _finding("entities.warning", Severity.WARNING),
        ],
    )

    domain = result.domain_health["entities"]

    assert domain["domain"] == "entities"
    assert domain["status"] == "checked"
    assert domain["checks"] == 1
    assert domain["findings"] == 1
    assert domain["health"]["score"] == 94


def test_as_dict_includes_domain_health() -> None:
    """Serialized results expose domain health summaries."""
    result = InspectionResult()

    payload = result.as_dict()

    assert payload["domain_health"] == result.domain_health



def test_remediation_workflow_diagnostics_are_serialized() -> None:
    """Inspection results expose remediation workflow diagnostics."""
    result = InspectionResult()
    result.remediation_workflow_diagnostics = {
        "affected_entities": 2,
        "review_required": 1,
        "likely_safe": 1,
        "affected_configurations": 3,
        "removable_references": 1,
        "review_references": 2,
        "entities": [
            {
                "entity_id": "sensor.missing",
                "action": "review_active_references",
                "safety": "review_required",
                "confidence": "high",
                "reference_count": 2,
                "active_reference_count": 2,
                "disabled_reference_count": 0,
                "affected_configuration_count": 2,
                "removable_reference_count": 0,
                "review_reference_count": 2,
                "projected_reference_count": 2,
            }
        ],
    }

    document = result.as_dict()

    assert document["remediation_workflow"] == {
        "affected_entities": 2,
        "review_required": 1,
        "likely_safe": 1,
        "affected_configurations": 3,
        "removable_references": 1,
        "review_references": 2,
        "entities": [
            {
                "entity_id": "sensor.missing",
                "action": "review_active_references",
                "safety": "review_required",
                "confidence": "high",
                "reference_count": 2,
                "active_reference_count": 2,
                "disabled_reference_count": 0,
                "affected_configuration_count": 2,
                "removable_reference_count": 0,
                "review_reference_count": 2,
                "projected_reference_count": 2,
            }
        ],
    }


def test_dashboard_summary_exposes_compact_health_state() -> None:
    """Dashboard summary exposes compact inspection health data."""
    result = InspectionResult()

    result.record_rule(
        category="system",
        weight=20,
        findings=[
            _finding("system.error", Severity.ERROR),
            _finding("system.warning", Severity.WARNING),
        ],
    )
    result.record_rule(
        category="entities",
        weight=10,
        findings=[
            _finding("entities.info", Severity.INFO),
        ],
    )

    summary = result.dashboard_summary

    assert summary["status"] == result.health_status.value
    assert summary["score"] == result.score
    assert summary["total_findings"] == 3
    assert summary["critical"] == 0
    assert summary["errors"] == 1
    assert summary["warnings"] == 1
    assert summary["info"] == 1
    assert summary["domains"] == result.domain_health


def test_dashboard_summary_for_empty_result() -> None:
    """Empty inspections expose a healthy empty dashboard summary."""
    result = InspectionResult()

    assert result.dashboard_summary == {
        "status": "excellent",
        "score": 100,
        "total_findings": 0,
        "critical": 0,
        "errors": 0,
        "warnings": 0,
        "info": 0,
        "dependencies": result.dependency_diagnostics,
        "domains": result.domain_health,
    }


def test_as_dict_includes_dashboard_summary() -> None:
    """Serialized results expose the dashboard summary."""
    result = InspectionResult()

    payload = result.as_dict()

    assert payload["dashboard_summary"] == result.dashboard_summary



def test_dashboard_summary_exposes_dependency_diagnostics() -> None:
    """Dashboard summary exposes compact dependency diagnostics."""
    result = InspectionResult(
        dependency_diagnostics={
            "affected_entities": 2,
            "unavailable": 1,
            "unknown": 1,
            "critical": 0,
            "high": 1,
            "medium": 1,
            "low": 0,
            "max_impact_score": 40,
        }
    )

    assert result.dashboard_summary["dependencies"] == {
        "affected_entities": 2,
        "unavailable": 1,
        "unknown": 1,
        "critical": 0,
        "high": 1,
        "medium": 1,
        "low": 0,
        "max_impact_score": 40,
    }


def test_resolved_remediation_items_are_serialized() -> None:
    """Resolved remediation items are included in the result document."""
    result = InspectionResult()
    result.resolved_remediation_items = (
        {
            "entity_id": "sensor.resolved",
            "completed_action_count": 2,
        },
    )

    document = result.as_dict()

    assert document["resolved_remediation_items"] == (
        {
            "entity_id": "sensor.resolved",
            "completed_action_count": 2,
        },
    )


def test_new_remediation_reference_items_are_serialized() -> None:
    """New remediation reference items are included in the result document."""
    result = InspectionResult()
    result.new_remediation_reference_items = (
        {
            "entity_id": "sensor.regressed",
            "new_reference_count": 2,
        },
    )

    document = result.as_dict()

    assert document["new_remediation_reference_items"] == (
        {
            "entity_id": "sensor.regressed",
            "new_reference_count": 2,
        },
    )


def test_remediation_lifecycle_summary_is_serialized() -> None:
    """Inspection result serializes remediation lifecycle summary."""
    result = InspectionResult()
    result.remediation_lifecycle_summary = {
        "status": "progressing",
        "tracked_entities": 2,
        "pending": 0,
        "in_progress": 1,
        "resolved": 1,
        "completed_actions": 1,
        "remaining_actions": 1,
        "new_references": 0,
        "resolved_since_previous": 1,
        "newly_pending_since_previous": 0,
        "new_references_delta": 0,
    }

    data = result.as_dict()

    assert data["remediation_lifecycle"] == {
        "status": "progressing",
        "tracked_entities": 2,
        "pending": 0,
        "in_progress": 1,
        "resolved": 1,
        "completed_actions": 1,
        "remaining_actions": 1,
        "new_references": 0,
        "resolved_since_previous": 1,
        "newly_pending_since_previous": 0,
        "new_references_delta": 0,
    }


def test_remediation_lifecycle_summary_defaults_to_idle() -> None:
    """Inspection result has an empty remediation lifecycle summary."""
    result = InspectionResult()

    assert result.as_dict()["remediation_lifecycle"] == {
        "status": "idle",
        "tracked_entities": 0,
        "pending": 0,
        "in_progress": 0,
        "resolved": 0,
        "completed_actions": 0,
        "remaining_actions": 0,
        "new_references": 0,
        "resolved_since_previous": 0,
        "newly_pending_since_previous": 0,
        "new_references_delta": 0,
    }
