"""Tests for typed system log state."""

from custom_components.ha_inspector.engine.logs_state import LogsState


def test_logs_state_defaults() -> None:
    state = LogsState()

    assert state.as_dict() == {
        "available": False,
        "warning_entries": 0,
        "error_entries": 0,
        "critical_entries": 0,
        "warning_occurrences": 0,
        "error_occurrences": 0,
        "critical_occurrences": 0,
        "top_loggers": [],
    }


def test_logs_state_serialization() -> None:
    state = LogsState(
        available=True,
        warning_entries=2,
        error_entries=1,
        warning_occurrences=5,
        error_occurrences=3,
        top_loggers=[
            {
                "logger": "homeassistant.components.example",
                "occurrences": 5,
            }
        ],
    )

    assert state.as_dict()["available"] is True
    assert state.as_dict()["warning_entries"] == 2
    assert state.as_dict()["error_entries"] == 1
    assert state.as_dict()["top_loggers"] == [
        {
            "logger": "homeassistant.components.example",
            "occurrences": 5,
        }
    ]
