"""Tests for RepairsState."""

from custom_components.ha_inspector.engine.repairs_state import RepairsState


def test_repairs_state_defaults() -> None:
    """Repairs state starts unavailable and empty."""
    state = RepairsState()

    assert state.available is False
    assert state.total == 0
    assert state.critical == 0
    assert state.error == 0
    assert state.warning == 0
    assert state.fixable == 0
    assert state.issues == []


def test_repairs_state_as_dict() -> None:
    """Repairs state serializes collected values."""
    state = RepairsState(
        available=True,
        total=2,
        critical=1,
        warning=1,
        fixable=1,
        issues=[
            {
                "domain": "demo",
                "issue_id": "critical_issue",
                "severity": "critical",
                "is_fixable": True,
                "breaks_in_ha_version": "2026.9.0",
            },
            {
                "domain": "other",
                "issue_id": "warning_issue",
                "severity": "warning",
                "is_fixable": False,
                "breaks_in_ha_version": None,
            },
        ],
    )

    data = state.as_dict()

    assert data["available"] is True
    assert data["total"] == 2
    assert data["critical"] == 1
    assert data["warning"] == 1
    assert data["fixable"] == 1
    assert len(data["issues"]) == 2
