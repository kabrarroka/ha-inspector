"""Tests for the typed backup state model."""

from custom_components.ha_inspector.engine.backup_state import BackupState


EXPECTED_BACKUP_KEYS = {
    "available",
    "reason",
    "count",
    "latest",
    "oldest",
    "agent_error_count",
    "agent_error_ids",
    "latest_backup_agent_count",
    "latest_backup_agent_ids",
    "latest_backup_failed_addons",
    "latest_backup_failed_folders",
    "latest_backup_failed_agent_ids",
}


def test_backup_state_defaults_match_collector_contract() -> None:
    state = BackupState()

    data = state.as_dict()

    assert set(data) == EXPECTED_BACKUP_KEYS
    assert data == {
        "available": False,
        "reason": None,
        "count": None,
        "latest": None,
        "oldest": None,
        "agent_error_count": 0,
        "agent_error_ids": [],
        "latest_backup_agent_count": None,
        "latest_backup_agent_ids": [],
        "latest_backup_failed_addons": [],
        "latest_backup_failed_folders": [],
        "latest_backup_failed_agent_ids": [],
    }


def test_backup_state_lists_are_not_shared() -> None:
    first = BackupState()
    second = BackupState()

    first.agent_error_ids.append("cloud")
    first.latest_backup_agent_ids.append("local")
    first.latest_backup_failed_addons.append("addon")
    first.latest_backup_failed_folders.append("media")
    first.latest_backup_failed_agent_ids.append("nas")

    assert second.agent_error_ids == []
    assert second.latest_backup_agent_ids == []
    assert second.latest_backup_failed_addons == []
    assert second.latest_backup_failed_folders == []
    assert second.latest_backup_failed_agent_ids == []


def test_backup_state_as_dict_returns_fresh_lists() -> None:
    state = BackupState(
        agent_error_ids=["cloud"],
        latest_backup_agent_ids=["local"],
    )

    first = state.as_dict()
    second = state.as_dict()

    first["agent_error_ids"].append("mutated")
    first["latest_backup_agent_ids"].append("mutated")

    assert second["agent_error_ids"] == ["cloud"]
    assert second["latest_backup_agent_ids"] == ["local"]