"""Home Assistant Repairs issue collector."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..context import InspectionContext
from ..repairs_state import RepairsState
from .base import BaseCollector

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


def _severity_value(value: object) -> str:
    """Return a normalized issue severity."""
    raw = getattr(value, "value", value)

    if isinstance(raw, str):
        return raw.strip().lower()

    return ""


def _collect_repairs_state(hass: HomeAssistant) -> RepairsState:
    """Collect active Home Assistant Repairs issues."""
    try:
        from homeassistant.helpers import issue_registry as ir
    except ImportError:
        return RepairsState()

    try:
        registry = ir.async_get(hass)
    except (KeyError, RuntimeError):
        return RepairsState()

    issues: list[dict[str, object]] = []

    counts = {
        "critical": 0,
        "error": 0,
        "warning": 0,
    }

    fixable = 0
    breaking = 0
    learn_more = 0

    for issue in registry.issues.values():
        if not issue.active:
            continue

        severity = _severity_value(issue.severity)

        if severity in counts:
            counts[severity] += 1

        if issue.is_fixable:
            fixable += 1

        if issue.breaks_in_ha_version:
            breaking += 1

        if issue.learn_more_url:
            learn_more += 1

        issues.append(
            {
                "domain": issue.domain,
                "issue_domain": issue.issue_domain,
                "issue_id": issue.issue_id,
                "severity": severity,
                "is_fixable": issue.is_fixable,
                "breaks_in_ha_version": issue.breaks_in_ha_version,
                "learn_more_url": issue.learn_more_url,
                "translation_key": issue.translation_key,
            }
        )

    issues.sort(
        key=lambda item: (
            str(item["severity"]),
            str(item["domain"]),
            str(item["issue_id"]),
        )
    )

    return RepairsState(
        available=True,
        total=len(issues),
        critical=counts["critical"],
        error=counts["error"],
        warning=counts["warning"],
        fixable=fixable,
        breaking=breaking,
        learn_more=learn_more,
        issues=issues,
    )


class RepairsCollector(BaseCollector):
    """Collect active Home Assistant Repairs issues."""

    collector_id = "repairs"

    async def collect(
        self,
        hass: HomeAssistant,
        context: InspectionContext,
    ) -> None:
        """Collect Repairs state."""
        context.repairs = _collect_repairs_state(hass)
