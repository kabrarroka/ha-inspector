from custom_components.ha_inspector.engine.integrations_state import (
    IntegrationsState,
    ProblematicIntegrationEntry,
)


def test_integrations_state_defaults() -> None:
    state = IntegrationsState()

    assert state.as_dict() == {
        "total_entries": 0,
        "states": {},
        "domains": {},
        "problematic_entries": [],
        "problematic_count": 0,
    }


def test_integrations_state_values() -> None:
    state = IntegrationsState(
        total_entries=3,
        states={
            "loaded": 2,
            "setup_error": 1,
        },
        domains={
            "mqtt": 1,
            "tuya": 2,
        },
        problematic_entries=[
            ProblematicIntegrationEntry(
                domain="tuya",
                title="Tuya",
                state="setup_error",
                reason="Authentication failed",
            )
        ],
        problematic_count=1,
    )

    assert state.as_dict() == {
        "total_entries": 3,
        "states": {
            "loaded": 2,
            "setup_error": 1,
        },
        "domains": {
            "mqtt": 1,
            "tuya": 2,
        },
        "problematic_entries": [
            {
                "domain": "tuya",
                "title": "Tuya",
                "state": "setup_error",
                "reason": "Authentication failed",
            }
        ],
        "problematic_count": 1,
    }