from custom_components.ha_inspector.engine.recorder_state import RecorderState


def test_recorder_state_defaults() -> None:
    state = RecorderState()

    assert state.as_dict() == {
        "available": False,
        "reason": None,
        "enabled": None,
        "recording": None,
        "is_running": None,
        "auto_purge": None,
        "auto_repack": None,
        "keep_days": None,
        "commit_interval": None,
        "backlog": None,
        "schema_version": None,
        "migration_in_progress": None,
        "migration_is_live": None,
        "database_dialect": None,
        "database_connected": None,
        "database_ready": None,
    }


def test_recorder_state_values() -> None:
    state = RecorderState(
        available=True,
        enabled=True,
        recording=True,
        is_running=True,
        auto_purge=True,
        auto_repack=False,
        keep_days=10,
        commit_interval=5,
        backlog=0,
        schema_version=42,
        migration_in_progress=False,
        migration_is_live=False,
        database_dialect="sqlite",
        database_connected=True,
        database_ready=True,
    )

    assert state.as_dict() == {
        "available": True,
        "reason": None,
        "enabled": True,
        "recording": True,
        "is_running": True,
        "auto_purge": True,
        "auto_repack": False,
        "keep_days": 10,
        "commit_interval": 5,
        "backlog": 0,
        "schema_version": 42,
        "migration_in_progress": False,
        "migration_is_live": False,
        "database_dialect": "sqlite",
        "database_connected": True,
        "database_ready": True,
    }

