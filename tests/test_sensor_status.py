"""Tests for the HA Inspector diagnostic sensor helpers."""

from custom_components.ha_inspector.sensor import status_from_summary


def test_status_is_ok_without_findings() -> None:
    """No findings should produce an OK status."""
    assert status_from_summary({}) == "ok"


def test_status_uses_highest_severity() -> None:
    """The highest present severity should win."""
    assert status_from_summary({"info": 3}) == "info"
    assert status_from_summary({"info": 3, "warning": 1}) == "warning"
    assert status_from_summary({"warning": 2, "error": 1}) == "error"
    assert status_from_summary({"error": 2, "critical": 1}) == "critical"


def test_status_accepts_zero_and_none_values() -> None:
    """Empty counter values should not change the status."""
    assert status_from_summary(
        {"info": None, "warning": 0, "error": 0, "critical": 0}
    ) == "ok"
