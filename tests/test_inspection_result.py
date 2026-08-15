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