"""Tests for rule execution result models."""

import pytest

from custom_components.ha_inspector.engine.models import Finding
from custom_components.ha_inspector.engine.result import (
    InspectionResult,
    RuleExecutionResult,
)
from custom_components.ha_inspector.engine.severity import Severity


def _finding() -> Finding:
    return Finding(
        finding_id="TEST_FINDING",
        severity=Severity.WARNING,
        title="Test finding",
        description="Finding used by result model tests.",
    )


def test_rule_execution_result_defaults_to_success() -> None:
    result = RuleExecutionResult(
        rule_id="system.test",
        duration_ms=1.25,
    )

    assert result.success is True
    assert result.failed is False
    assert result.finding_count == 0
    assert result.error is None


def test_rule_execution_result_serializes_findings() -> None:
    result = RuleExecutionResult(
        rule_id="system.test",
        duration_ms=2.5,
        findings=(_finding(),),
    )

    serialized = result.as_dict()

    assert serialized["rule_id"] == "system.test"
    assert serialized["duration_ms"] == 2.5
    assert serialized["finding_count"] == 1
    assert serialized["success"] is True
    assert serialized["findings"][0]["id"] == "TEST_FINDING"


def test_failed_rule_execution_requires_error() -> None:
    with pytest.raises(ValueError):
        RuleExecutionResult(
            rule_id="system.test",
            duration_ms=1.0,
            success=False,
        )


def test_successful_rule_execution_rejects_error() -> None:
    with pytest.raises(ValueError):
        RuleExecutionResult(
            rule_id="system.test",
            duration_ms=1.0,
            error="unexpected",
        )


@pytest.mark.parametrize(
    ("rule_id", "duration_ms"),
    [
        ("", 0.0),
        ("   ", 0.0),
        ("system.test", -0.1),
    ],
)
def test_rule_execution_rejects_invalid_identity_or_duration(
    rule_id: str,
    duration_ms: float,
) -> None:
    with pytest.raises(ValueError):
        RuleExecutionResult(
            rule_id=rule_id,
            duration_ms=duration_ms,
        )


def test_existing_inspection_result_api_remains_available() -> None:
    finding = _finding()
    result = InspectionResult()

    result.record_rule(
        category="system",
        weight=10,
        findings=[finding],
    )
    result.finish()

    assert result.checks_executed == 1
    assert result.total_findings == 1
    assert result.categories["system"]["checks"] == 1
    assert result.as_dict()["schema_version"] == 2
