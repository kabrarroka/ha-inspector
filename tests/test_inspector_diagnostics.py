from __future__ import annotations

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.inspector import Inspector
from custom_components.ha_inspector.engine.storage_state import StorageState
from custom_components.ha_inspector.engine.system_state import SystemState


def test_diagnostic_context_serializes_typed_states() -> None:
    context = InspectionContext(
        system=SystemState(
            home_assistant_version="2026.8.0",
            architecture="x86_64",
            latitude=41.65,
            longitude=-4.72,
            internal_url="http://homeassistant.local:8123",
            external_url="https://example.ui.nabu.casa",
            config_directory="/config",
            python_executable="/usr/bin/python3",
        ),
        storage=StorageState(
            total_bytes=1000,
            used_bytes=400,
            free_bytes=600,
            free_percent=60.0,
        ),
    )

    diagnostic = Inspector._diagnostic_context(context)

    system = diagnostic["system"]

    assert isinstance(system, dict)
    assert system["home_assistant_version"] == "2026.8.0"
    assert system["architecture"] == "x86_64"

    assert "latitude" not in system
    assert "longitude" not in system
    assert "internal_url" not in system
    assert "external_url" not in system
    assert "config_directory" not in system
    assert "python_executable" not in system

    assert diagnostic["storage"] == {
        "total_bytes": 1000,
        "used_bytes": 400,
        "free_bytes": 600,
        "free_percent": 60.0,
    }

    assert isinstance(diagnostic["logs"], dict)
    assert isinstance(diagnostic["addons"], dict)
    assert isinstance(diagnostic["backups"], dict)
    assert isinstance(diagnostic["recorder"], dict)
    assert isinstance(diagnostic["integrations"], dict)
    assert isinstance(diagnostic["entities"], dict)