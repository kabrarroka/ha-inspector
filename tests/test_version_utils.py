"""Tests for Home Assistant version parsing utilities."""

from custom_components.ha_inspector.engine.utils.versions import (
    VersionKind,
    parse_home_assistant_version,
)


def test_parse_stable_version() -> None:
    """A normal release must be classified as stable."""
    result = parse_home_assistant_version("2026.7.2")

    assert result.raw == "2026.7.2"
    assert result.kind is VersionKind.STABLE
    assert result.prerelease is None


def test_parse_beta_version() -> None:
    """A beta release must expose its prerelease identifier."""
    result = parse_home_assistant_version("2026.8.0b7")

    assert result.kind is VersionKind.BETA
    assert result.prerelease == "b7"


def test_parse_release_candidate() -> None:
    """A release candidate must be classified as RC."""
    result = parse_home_assistant_version("2026.8.0rc2")

    assert result.kind is VersionKind.RC
    assert result.prerelease == "rc2"


def test_parse_development_version() -> None:
    """A development release must be classified as dev."""
    result = parse_home_assistant_version("2026.8.0.dev0")

    assert result.kind is VersionKind.DEV
    assert result.prerelease == "dev0"


def test_parse_none_version() -> None:
    """A missing version must be unknown."""
    result = parse_home_assistant_version(None)

    assert result.raw is None
    assert result.kind is VersionKind.UNKNOWN
    assert result.prerelease is None


def test_parse_empty_version() -> None:
    """An empty version must be unknown."""
    result = parse_home_assistant_version("")

    assert result.kind is VersionKind.UNKNOWN


def test_parse_whitespace_version() -> None:
    """Whitespace-only input must be unknown."""
    result = parse_home_assistant_version("   ")

    assert result.kind is VersionKind.UNKNOWN


def test_parse_unexpected_format() -> None:
    """An unsupported format must not be mistaken for stable."""
    result = parse_home_assistant_version("not-a-version")

    assert result.kind is VersionKind.UNKNOWN


def test_parse_version_with_surrounding_whitespace() -> None:
    """Valid versions may contain harmless surrounding whitespace."""
    result = parse_home_assistant_version(" 2026.8.0b3 ")

    assert result.kind is VersionKind.BETA
    assert result.prerelease == "b3"
