"""Tests for historical inspection comparison."""

from custom_components.ha_inspector.engine.historical_comparison import (
    HistoricalInspectionComparison,
    compare_history_entries,
)


def test_compare_history_entries() -> None:
    comparison = compare_history_entries(
        {
            "score": 80,
            "status": "warning",
            "total_findings": 5,
        },
        {
            "score": 95,
            "status": "healthy",
            "total_findings": 2,
        },
    )

    assert comparison == HistoricalInspectionComparison(
        previous_score=80,
        current_score=95,
        score_delta=15,
        previous_status="warning",
        current_status="healthy",
        previous_findings=5,
        current_findings=2,
        findings_delta=-3,
    )


def test_compare_history_entries_handles_missing_values() -> None:
    comparison = compare_history_entries(
        {},
        {
            "score": 90,
            "status": "healthy",
        },
    )

    assert comparison.previous_score is None
    assert comparison.current_score == 90
    assert comparison.score_delta is None
    assert comparison.previous_status is None
    assert comparison.current_status == "healthy"
    assert comparison.previous_findings is None
    assert comparison.current_findings is None
    assert comparison.findings_delta is None


def test_compare_history_entries_rejects_invalid_values() -> None:
    comparison = compare_history_entries(
        {
            "score": True,
            "status": 123,
            "total_findings": "5",
        },
        {
            "score": "90",
            "status": None,
            "total_findings": False,
        },
    )

    assert comparison.previous_score is None
    assert comparison.current_score is None
    assert comparison.score_delta is None
    assert comparison.previous_status is None
    assert comparison.current_status is None
    assert comparison.previous_findings is None
    assert comparison.current_findings is None
    assert comparison.findings_delta is None


def test_historical_comparison_serializes() -> None:
    comparison = HistoricalInspectionComparison(
        previous_score=80,
        current_score=90,
        score_delta=10,
        previous_status="warning",
        current_status="healthy",
        previous_findings=4,
        current_findings=2,
        findings_delta=-2,
    )

    assert comparison.as_dict() == {
        "previous_score": 80,
        "current_score": 90,
        "score_delta": 10,
        "previous_status": "warning",
        "current_status": "healthy",
        "previous_findings": 4,
        "current_findings": 2,
        "findings_delta": -2,
    }


def test_compare_history_domains() -> None:
    from custom_components.ha_inspector.engine.historical_comparison import (
        compare_history_domains,
    )

    comparisons = compare_history_domains(
        {
            "domain_health": {
                "storage": {
                    "health": {
                        "score": 70,
                        "status": "warning",
                    }
                },
                "system": {
                    "health": {
                        "score": 95,
                        "status": "excellent",
                    }
                },
            }
        },
        {
            "domain_health": {
                "storage": {
                    "health": {
                        "score": 90,
                        "status": "excellent",
                    }
                },
                "system": {
                    "health": {
                        "score": 80,
                        "status": "good",
                    }
                },
            }
        },
    )

    assert comparisons["storage"].score_delta == 20
    assert comparisons["storage"].previous_status == "warning"
    assert comparisons["storage"].current_status == "excellent"

    assert comparisons["system"].score_delta == -15
    assert comparisons["system"].previous_status == "excellent"
    assert comparisons["system"].current_status == "good"


def test_compare_history_domains_handles_added_and_removed_domains() -> None:
    from custom_components.ha_inspector.engine.historical_comparison import (
        compare_history_domains,
    )

    comparisons = compare_history_domains(
        {
            "domain_health": {
                "storage": {
                    "health": {
                        "score": 80,
                        "status": "good",
                    }
                }
            }
        },
        {
            "domain_health": {
                "system": {
                    "health": {
                        "score": 90,
                        "status": "excellent",
                    }
                }
            }
        },
    )

    assert comparisons["storage"].previous_score == 80
    assert comparisons["storage"].current_score is None
    assert comparisons["storage"].score_delta is None

    assert comparisons["system"].previous_score is None
    assert comparisons["system"].current_score == 90
    assert comparisons["system"].score_delta is None


def test_compare_history_domains_handles_invalid_data() -> None:
    from custom_components.ha_inspector.engine.historical_comparison import (
        compare_history_domains,
    )

    comparisons = compare_history_domains(
        {
            "domain_health": "invalid",
        },
        {
            "domain_health": {
                123: {
                    "health": {
                        "score": 90,
                    }
                },
                "system": "invalid",
                "storage": {
                    "status": "not_checked",
                    "health": None,
                },
            }
        },
    )

    assert list(comparisons) == ["storage"]
    assert comparisons["storage"].previous_score is None
    assert comparisons["storage"].current_score is None
    assert comparisons["storage"].current_status == "not_checked"


def test_historical_domain_comparison_serializes() -> None:
    from custom_components.ha_inspector.engine.historical_comparison import (
        HistoricalDomainComparison,
    )

    comparison = HistoricalDomainComparison(
        domain="system",
        previous_score=80,
        current_score=90,
        score_delta=10,
        previous_status="good",
        current_status="excellent",
    )

    assert comparison.as_dict() == {
        "domain": "system",
        "previous_score": 80,
        "current_score": 90,
        "score_delta": 10,
        "previous_status": "good",
        "current_status": "excellent",
    }


def test_compare_remediation_history() -> None:
    from custom_components.ha_inspector.engine.historical_comparison import (
        HistoricalRemediationComparison,
        compare_remediation_history,
    )

    comparison = compare_remediation_history(
        {
            "remediation": {
                "tracked_entities": 4,
                "pending": 3,
                "in_progress": 1,
                "resolved": 0,
                "completed_actions": 1,
                "remaining_actions": 5,
                "new_references": 0,
            }
        },
        {
            "remediation": {
                "tracked_entities": 4,
                "pending": 1,
                "in_progress": 1,
                "resolved": 2,
                "completed_actions": 4,
                "remaining_actions": 2,
                "new_references": 1,
            }
        },
    )

    assert comparison == HistoricalRemediationComparison(
        previous_tracked_entities=4,
        current_tracked_entities=4,
        tracked_entities_delta=0,
        previous_pending=3,
        current_pending=1,
        pending_delta=-2,
        previous_in_progress=1,
        current_in_progress=1,
        in_progress_delta=0,
        previous_resolved=0,
        current_resolved=2,
        resolved_delta=2,
        previous_completed_actions=1,
        current_completed_actions=4,
        completed_actions_delta=3,
        previous_remaining_actions=5,
        current_remaining_actions=2,
        remaining_actions_delta=-3,
        previous_new_references=0,
        current_new_references=1,
        new_references_delta=1,
    )


def test_compare_remediation_history_handles_missing_values() -> None:
    from custom_components.ha_inspector.engine.historical_comparison import (
        compare_remediation_history,
    )

    comparison = compare_remediation_history(
        {},
        {
            "remediation": {
                "tracked_entities": 2,
                "resolved": 1,
            }
        },
    )

    assert comparison.previous_tracked_entities is None
    assert comparison.current_tracked_entities == 2
    assert comparison.tracked_entities_delta is None

    assert comparison.previous_resolved is None
    assert comparison.current_resolved == 1
    assert comparison.resolved_delta is None

    assert comparison.previous_pending is None
    assert comparison.current_pending is None


def test_compare_remediation_history_rejects_invalid_values() -> None:
    from custom_components.ha_inspector.engine.historical_comparison import (
        compare_remediation_history,
    )

    comparison = compare_remediation_history(
        {
            "remediation": {
                "tracked_entities": True,
                "pending": "3",
                "resolved": 1.5,
            }
        },
        {
            "remediation": "invalid",
        },
    )

    assert comparison.previous_tracked_entities is None
    assert comparison.current_tracked_entities is None
    assert comparison.previous_pending is None
    assert comparison.current_pending is None
    assert comparison.previous_resolved is None
    assert comparison.current_resolved is None


def test_historical_remediation_comparison_serializes() -> None:
    from custom_components.ha_inspector.engine.historical_comparison import (
        HistoricalRemediationComparison,
    )

    comparison = HistoricalRemediationComparison(
        previous_tracked_entities=4,
        current_tracked_entities=3,
        tracked_entities_delta=-1,
        previous_pending=2,
        current_pending=1,
        pending_delta=-1,
        previous_in_progress=1,
        current_in_progress=1,
        in_progress_delta=0,
        previous_resolved=1,
        current_resolved=1,
        resolved_delta=0,
        previous_completed_actions=2,
        current_completed_actions=3,
        completed_actions_delta=1,
        previous_remaining_actions=4,
        current_remaining_actions=2,
        remaining_actions_delta=-2,
        previous_new_references=0,
        current_new_references=1,
        new_references_delta=1,
    )

    assert comparison.as_dict() == {
        "previous_tracked_entities": 4,
        "current_tracked_entities": 3,
        "tracked_entities_delta": -1,
        "previous_pending": 2,
        "current_pending": 1,
        "pending_delta": -1,
        "previous_in_progress": 1,
        "current_in_progress": 1,
        "in_progress_delta": 0,
        "previous_resolved": 1,
        "current_resolved": 1,
        "resolved_delta": 0,
        "previous_completed_actions": 2,
        "current_completed_actions": 3,
        "completed_actions_delta": 1,
        "previous_remaining_actions": 4,
        "current_remaining_actions": 2,
        "remaining_actions_delta": -2,
        "previous_new_references": 0,
        "current_new_references": 1,
        "new_references_delta": 1,
    }
