"""Utilities for parsing Home Assistant version strings."""

from __future__ import annotations

from dataclasses import dataclass
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


_VERSION_PATTERN = re.compile(
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


def parse_home_assistant_version(version: str | None) -> VersionInfo:
    """Parse a Home Assistant Core version.

    Supported examples:
    - ``2026.7.2``
    - ``2026.8.0b3``
    - ``2026.8.0rc2``
    - ``2026.8.0.dev0``

    Empty values and unrecognized formats are returned as ``UNKNOWN``.
    """
    if version is None:
        return VersionInfo(raw=None, kind=VersionKind.UNKNOWN)

    raw = version.strip()
    if not raw:
        return VersionInfo(raw=version, kind=VersionKind.UNKNOWN)

    match = _VERSION_PATTERN.fullmatch(raw)
    if match is None:
        return VersionInfo(raw=version, kind=VersionKind.UNKNOWN)

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
