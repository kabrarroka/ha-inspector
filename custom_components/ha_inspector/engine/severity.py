"""Severity levels used by HA Inspector."""

from __future__ import annotations

from enum import IntEnum


class Severity(IntEnum):
    """Severity level of an inspection finding."""

    INFO = 0
    WARNING = 1
    ERROR = 2
    CRITICAL = 3

    @property
    def label(self) -> str:
        """Return a human-readable severity label."""
        return self.name.lower()

    @property
    def icon(self) -> str:
        """Return the Material Design icon for this severity."""
        return {
            Severity.INFO: "mdi:information-outline",
            Severity.WARNING: "mdi:alert-outline",
            Severity.ERROR: "mdi:alert-circle-outline",
            Severity.CRITICAL: "mdi:alert-octagon-outline",
        }[self]