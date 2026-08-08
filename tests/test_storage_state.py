from custom_components.ha_inspector.engine.storage_state import StorageState


def test_storage_state_defaults() -> None:
    state = StorageState()

    assert state.as_dict() == {
        "total_bytes": 0,
        "used_bytes": 0,
        "free_bytes": 0,
        "free_percent": 0.0,
    }


def test_storage_state_values() -> None:
    state = StorageState(
        total_bytes=1000,
        used_bytes=400,
        free_bytes=600,
        free_percent=60.0,
    )

    assert state.as_dict() == {
        "total_bytes": 1000,
        "used_bytes": 400,
        "free_bytes": 600,
        "free_percent": 60.0,
    }
