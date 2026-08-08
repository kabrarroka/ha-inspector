from custom_components.ha_inspector.engine.system_state import SystemState


def test_system_state_defaults() -> None:
    state = SystemState()

    assert state.as_dict() == {
        "home_assistant_version": "",
        "python_version": "",
        "python_implementation": "",
        "architecture": "",
        "platform": "",
        "platform_release": "",
        "timezone": None,
        "latitude": None,
        "longitude": None,
        "elevation": None,
        "currency": None,
        "country": None,
        "language": None,
        "config_directory": "",
        "internal_url": None,
        "external_url": None,
        "python_executable": "",
    }


def test_system_state_values() -> None:
    state = SystemState(
        home_assistant_version="2026.8.0",
        python_version="3.14.7",
        python_implementation="CPython",
        architecture="x86_64",
        platform="Linux",
        platform_release="6.8.0",
        timezone="Europe/Madrid",
        latitude=41.65,
        longitude=-4.72,
        elevation=700,
        currency="EUR",
        country="ES",
        language="es",
        config_directory="/config",
        internal_url="http://homeassistant.local:8123",
        external_url="https://example.ui.nabu.casa",
        python_executable="/usr/local/bin/python",
    )

    assert state.as_dict() == {
        "home_assistant_version": "2026.8.0",
        "python_version": "3.14.7",
        "python_implementation": "CPython",
        "architecture": "x86_64",
        "platform": "Linux",
        "platform_release": "6.8.0",
        "timezone": "Europe/Madrid",
        "latitude": 41.65,
        "longitude": -4.72,
        "elevation": 700,
        "currency": "EUR",
        "country": "ES",
        "language": "es",
        "config_directory": "/config",
        "internal_url": "http://homeassistant.local:8123",
        "external_url": "https://example.ui.nabu.casa",
        "python_executable": "/usr/local/bin/python",
    }
    