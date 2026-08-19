"""Supervisor add-on collector for HA Inspector."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..addons_state import AddonsState
from ..context import InspectionContext
from .base import BaseCollector

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


def _normalize_state(value: object) -> str | None:
    """Normalize a Supervisor add-on state."""
    raw = getattr(value, "value", value)

    if not isinstance(raw, str):
        return None

    normalized = raw.strip().lower()

    return normalized or None


def _collect_addons_state(hass: HomeAssistant) -> AddonsState:
    """Collect Supervisor add-on health information."""
    try:
        from homeassistant.components.hassio.coordinator import get_addons_list
        from homeassistant.components.hassio.exceptions import (
            HassioNotReadyError,
        )
    except ImportError:
        return AddonsState()

    try:
        addons = get_addons_list(hass)
    except HassioNotReadyError:
        return AddonsState()

    counts = {
        "started": 0,
        "startup": 0,
        "stopped": 0,
        "unknown": 0,
        "error": 0,
    }

    problematic: list[dict[str, str]] = []
    updates_available: list[dict[str, str]] = []

    for addon in addons:
        slug = addon.get("slug")
        name = addon.get("name")
        state = _normalize_state(addon.get("state"))

        addon_slug = slug if isinstance(slug, str) else ""
        addon_name = name if isinstance(name, str) else addon_slug

        if state in counts:
            counts[state] += 1

        if state in {"error", "unknown"}:
            problematic.append(
                {
                    "slug": addon_slug,
                    "name": addon_name,
                    "state": state,
                }
            )

        if addon.get("update_available") is True:
            version = addon.get("version")
            version_latest = addon.get("version_latest")

            updates_available.append(
                {
                    "slug": addon_slug,
                    "name": addon_name,
                    "version": (
                        version if isinstance(version, str) else ""
                    ),
                    "version_latest": (
                        version_latest
                        if isinstance(version_latest, str)
                        else ""
                    ),
                }
            )

    problematic.sort(
        key=lambda item: (
            item["state"],
            item["name"],
            item["slug"],
        )
    )
    updates_available.sort(
        key=lambda item: (
            item["name"],
            item["slug"],
        )
    )

    return AddonsState(
        available=True,
        total=len(addons),
        started=counts["started"],
        startup=counts["startup"],
        stopped=counts["stopped"],
        unknown=counts["unknown"],
        error=counts["error"],
        problematic=problematic,
        updates_available=updates_available,
    )


class AddonsCollector(BaseCollector):
    """Collect Home Assistant Supervisor add-on health."""

    collector_id = "addons"

    async def collect(
        self,
        hass: HomeAssistant,
        context: InspectionContext,
    ) -> None:
        """Collect Supervisor add-on state."""
        context.addons = _collect_addons_state(hass)
