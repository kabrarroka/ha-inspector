"""Tests for Supervisor add-on collector."""

from enum import Enum

from custom_components.ha_inspector.engine.collectors import addons as addon_module


class FakeState(Enum):
    STARTED = "started"
    ERROR = "error"


def test_normalize_addon_state() -> None:
    assert addon_module._normalize_state("started") == "started"
    assert addon_module._normalize_state(FakeState.ERROR) == "error"
    assert addon_module._normalize_state(None) is None


def test_collect_addons_state(monkeypatch) -> None:
    addons = [
        {
            "slug": "mosquitto",
            "name": "Mosquitto broker",
            "state": FakeState.STARTED,
            "update_available": False,
            "version": "1.0",
            "version_latest": "1.0",
        },
        {
            "slug": "broken",
            "name": "Broken add-on",
            "state": FakeState.ERROR,
            "update_available": True,
            "version": "1.0",
            "version_latest": "1.1",
        },
        {
            "slug": "manual",
            "name": "Manual add-on",
            "state": "stopped",
            "update_available": False,
        },
    ]

    class FakeNotReadyError(Exception):
        pass

    def fake_get_addons_list(hass):
        return addons

    monkeypatch.setitem(
        __import__("sys").modules,
        "homeassistant.components.hassio.coordinator",
        type(
            "CoordinatorModule",
            (),
            {"get_addons_list": staticmethod(fake_get_addons_list)},
        )(),
    )
    monkeypatch.setitem(
        __import__("sys").modules,
        "homeassistant.components.hassio.exceptions",
        type(
            "ExceptionsModule",
            (),
            {"HassioNotReadyError": FakeNotReadyError},
        )(),
    )

    state = addon_module._collect_addons_state(object())

    assert state.available is True
    assert state.total == 3
    assert state.started == 1
    assert state.stopped == 1
    assert state.error == 1
    assert state.unknown == 0

    assert state.problematic == [
        {
            "slug": "broken",
            "name": "Broken add-on",
            "state": "error",
        }
    ]

    assert state.updates_available == [
        {
            "slug": "broken",
            "name": "Broken add-on",
            "version": "1.0",
            "version_latest": "1.1",
        }
    ]


def test_stopped_addon_is_not_problematic(monkeypatch) -> None:
    addons = [
        {
            "slug": "manual",
            "name": "Manual add-on",
            "state": "stopped",
            "update_available": False,
        }
    ]

    class FakeNotReadyError(Exception):
        pass

    monkeypatch.setitem(
        __import__("sys").modules,
        "homeassistant.components.hassio.coordinator",
        type(
            "CoordinatorModule",
            (),
            {"get_addons_list": staticmethod(lambda hass: addons)},
        )(),
    )
    monkeypatch.setitem(
        __import__("sys").modules,
        "homeassistant.components.hassio.exceptions",
        type(
            "ExceptionsModule",
            (),
            {"HassioNotReadyError": FakeNotReadyError},
        )(),
    )

    state = addon_module._collect_addons_state(object())

    assert state.stopped == 1
    assert state.problematic == []
