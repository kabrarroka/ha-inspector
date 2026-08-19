"""Tests for typed add-on health state."""

from custom_components.ha_inspector.engine.addons_state import AddonsState


def test_addons_state_defaults() -> None:
    state = AddonsState()

    assert state.as_dict() == {
        "available": False,
        "total": 0,
        "started": 0,
        "startup": 0,
        "stopped": 0,
        "unknown": 0,
        "error": 0,
        "problematic": [],
        "updates_available": [],
    }


def test_addons_state_serialization() -> None:
    state = AddonsState(
        available=True,
        total=2,
        started=1,
        error=1,
        problematic=[
            {
                "slug": "broken",
                "name": "Broken add-on",
                "state": "error",
            }
        ],
    )

    payload = state.as_dict()

    assert payload["available"] is True
    assert payload["total"] == 2
    assert payload["error"] == 1
    assert payload["problematic"] == [
        {
            "slug": "broken",
            "name": "Broken add-on",
            "state": "error",
        }
    ]
