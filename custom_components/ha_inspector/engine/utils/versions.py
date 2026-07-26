"""Utilities for parsing Home Assistant version strings."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
import re


class VersionKind(str, Enum):
    """Kinds of Home Assistant releases recognized by HA Inspector."""

    STABLE = "stable"
    BETA = "beta"
    RC = "rc"
    DEV = "dev"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class VersionInfo:
    """Normalized information extracted from a version string."""

    raw: str | None
    kind: VersionKind
    prerelease: str | None = None


_CORE_VERSION_PATTERN = re.compile(
    r"""
    ^
    (?P<year>\d{4})
    \.
    (?P<month>\d{1,2})
    \.
    (?P<patch>\d+)
    (?:
        (?P<beta>b\d+)
        |
        (?P<rc>rc\d+)
        |
        \.?(?P<dev>dev\d*)
    )?
    $
    """,
    re.IGNORECASE | re.VERBOSE,
)

_OS_VERSION_PATTERN = re.compile(
    r"""
    ^
    (?P<major>\d+)
    \.
    (?P<minor>\d+)
    (?:
        \.
        (?:
            (?P<beta>beta\d+|b\d+)
            |
            (?P<rc>rc\d+)
            |
            (?P<dev>dev\d*)
        )
    )?
    $
    """,
    re.IGNORECASE | re.VERBOSE,
)

_FRONTEND_VERSION_PATTERN = re.compile(
    r"""
    ^
    (?P<year>\d{4})
    (?P<month>\d{2})
    (?P<day>\d{2})
    \.
    (?P<revision>\d+)
    $
    """,
    re.VERBOSE,
)


def _unknown(version: str | None) -> VersionInfo:
    """Return a normalized unknown version result."""
    return VersionInfo(raw=version, kind=VersionKind.UNKNOWN)


def _classify_match(
    version: str,
    match: re.Match[str],
) -> VersionInfo:
    """Convert a successful prerelease regex match into VersionInfo."""
    if prerelease := match.group("beta"):
        return VersionInfo(
            raw=version,
            kind=VersionKind.BETA,
            prerelease=prerelease.lower(),
        )

    if prerelease := match.group("rc"):
        return VersionInfo(
            raw=version,
            kind=VersionKind.RC,
            prerelease=prerelease.lower(),
        )

    if prerelease := match.group("dev"):
        return VersionInfo(
            raw=version,
            kind=VersionKind.DEV,
            prerelease=prerelease.lower(),
        )

    return VersionInfo(raw=version, kind=VersionKind.STABLE)


def parse_home_assistant_version(version: str | None) -> VersionInfo:
    """Parse a Home Assistant Core or Supervisor version."""
    if version is None:
        return _unknown(None)

    raw = version.strip()
    if not raw:
        return _unknown(version)

    match = _CORE_VERSION_PATTERN.fullmatch(raw)
    if match is None:
        return _unknown(version)

    return _classify_match(version, match)


def parse_home_assistant_os_version(
    version: str | None,
) -> VersionInfo:
    """Parse a Home Assistant Operating System version."""
    if version is None:
        return _unknown(None)

    raw = version.strip()
    if not raw:
        return _unknown(version)

    match = _OS_VERSION_PATTERN.fullmatch(raw)
    if match is None:
        return _unknown(version)

    return _classify_match(version, match)


def parse_home_assistant_frontend_version(
    version: str | None,
) -> VersionInfo:
    """Parse a Home Assistant Frontend version.

    Frontend versions use a date and revision, for example
    ``20260624.5``. The version string does not reliably identify whether
    the corresponding GitHub release was stable or a prerelease, so every
    valid format is classified as ``STABLE`` for parser compatibility.
    """
    if version is None:
        return _unknown(None)

    raw = version.strip()
    if not raw:
        return _unknown(version)

    match = _FRONTEND_VERSION_PATTERN.fullmatch(raw)
    if match is None:
        return _unknown(version)

    try:
        date(
            int(match.group("year")),
            int(match.group("month")),
            int(match.group("day")),
        )
    except ValueError:
        return _unknown(version)

    return VersionInfo(raw=version, kind=VersionKind.STABLE)
