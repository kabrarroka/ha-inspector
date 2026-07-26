"""Tests for Home Assistant version parsing utilities."""

from custom_components.ha_inspector.engine.utils.versions import (
    VersionKind,
    parse_home_assistant_frontend_version,
    parse_home_assistant_os_version,
    parse_home_assistant_version,
)


def test_parse_stable_version() -> None:
    result = parse_home_assistant_version("2026.7.2")
    assert result.kind is VersionKind.STABLE


def test_parse_beta_version() -> None:
    result = parse_home_assistant_version("2026.8.0b7")
    assert result.kind is VersionKind.BETA
    assert result.prerelease == "b7"


def test_parse_release_candidate() -> None:
    result = parse_home_assistant_version("2026.8.0rc2")
    assert result.kind is VersionKind.RC


def test_parse_development_version() -> None:
    result = parse_home_assistant_version("2026.8.0.dev0")
    assert result.kind is VersionKind.DEV


def test_parse_none_version() -> None:
    assert parse_home_assistant_version(None).kind is VersionKind.UNKNOWN


def test_parse_empty_version() -> None:
    assert parse_home_assistant_version("").kind is VersionKind.UNKNOWN


def test_parse_unexpected_format() -> None:
    result = parse_home_assistant_version("not-a-version")
    assert result.kind is VersionKind.UNKNOWN


def test_parse_stable_os_version() -> None:
    result = parse_home_assistant_os_version("18.1")
    assert result.kind is VersionKind.STABLE


def test_parse_os_release_candidate() -> None:
    result = parse_home_assistant_os_version("17.3.rc1")
    assert result.kind is VersionKind.RC


def test_parse_os_beta_version() -> None:
    result = parse_home_assistant_os_version("18.0.beta2")
    assert result.kind is VersionKind.BETA


def test_parse_os_development_version() -> None:
    result = parse_home_assistant_os_version("18.0.dev0")
    assert result.kind is VersionKind.DEV


def test_parse_invalid_os_version() -> None:
    result = parse_home_assistant_os_version("2026.8.0")
    assert result.kind is VersionKind.UNKNOWN


def test_parse_frontend_version() -> None:
    result = parse_home_assistant_frontend_version("20260624.5")
    assert result.raw == "20260624.5"
    assert result.kind is VersionKind.STABLE


def test_parse_frontend_first_revision() -> None:
    result = parse_home_assistant_frontend_version("20260723.0")
    assert result.kind is VersionKind.STABLE


def test_parse_invalid_frontend_date() -> None:
    result = parse_home_assistant_frontend_version("20260230.1")
    assert result.kind is VersionKind.UNKNOWN


def test_parse_invalid_frontend_format() -> None:
    result = parse_home_assistant_frontend_version("2026.7.2")
    assert result.kind is VersionKind.UNKNOWN


def test_parse_missing_frontend_version() -> None:
    assert (
        parse_home_assistant_frontend_version(None).kind
        is VersionKind.UNKNOWN
    )
