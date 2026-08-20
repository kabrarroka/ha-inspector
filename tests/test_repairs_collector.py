"""Tests for the Home Assistant Repairs collector."""

from types import SimpleNamespace
from typing import Any

import pytest

from custom_components.ha_inspector.engine.collectors.repairs import (
    RepairsCollector,
    _collect_repairs_state,
    _severity_value,
)
from custom_components.ha_inspector.engine.context import InspectionContext


def _issue(
    *,
    domain: str,
    issue_id: str,
    severity: str,
    active: bool = True,
    is_fixable: bool = False,
    breaks_in_ha_version: str | None = None,
) -> SimpleNamespace:
    """Create a fake Home Assistant issue registry entry."""
    return SimpleNamespace(
        domain=domain,
        issue_id=issue_id,
        severity=SimpleNamespace(value=severity),
        active=active,
        is_fixable=is_fixable,
        breaks_in_ha_version=breaks_in_ha_version,
    )


def test_severity_value_normalizes_enum_like_value() -> None:
    """Severity values are normalized from enum-like objects."""
    value = SimpleNamespace(value=" WARNING ")

    assert _severity_value(value) == "warning"


def test_severity_value_rejects_non_string_values() -> None:
    """Non-string severity values produce an empty severity."""
    assert _severity_value(123) == ""
    assert _severity_value(SimpleNamespace(value=None)) == ""


def test_collect_repairs_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Active Repairs issues are collected and summarized."""
    from homeassistant.helpers import issue_registry as ir

    registry = SimpleNamespace(
        issues={
            ("demo", "warning"): _issue(
                domain="demo",
                issue_id="warning",
                severity="warning",
                is_fixable=False,
            ),
            ("demo", "critical"): _issue(
                domain="demo",
                issue_id="critical",
                severity="critical",
                is_fixable=True,
                breaks_in_ha_version="2026.9.0",
            ),
            ("other", "error"): _issue(
                domain="other",
                issue_id="error",
                severity="error",
                is_fixable=True,
            ),
            ("other", "inactive"): _issue(
                domain="other",
                issue_id="inactive",
                severity="warning",
                active=False,
                is_fixable=True,
            ),
        }
    )

    monkeypatch.setattr(ir, "async_get", lambda hass: registry)

    state = _collect_repairs_state(SimpleNamespace())

    assert state.available is True
    assert state.total == 3
    assert state.critical == 1
    assert state.error == 1
    assert state.warning == 1
    assert state.fixable == 2

    assert state.issues == [
        {
            "domain": "demo",
            "issue_id": "critical",
            "severity": "critical",
            "is_fixable": True,
            "breaks_in_ha_version": "2026.9.0",
        },
        {
            "domain": "other",
            "issue_id": "error",
            "severity": "error",
            "is_fixable": True,
            "breaks_in_ha_version": None,
        },
        {
            "domain": "demo",
            "issue_id": "warning",
            "severity": "warning",
            "is_fixable": False,
            "breaks_in_ha_version": None,
        },
    ]


def test_collect_repairs_state_registry_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Registry access failures return the default unavailable state."""
    from homeassistant.helpers import issue_registry as ir

    def _raise(_: Any) -> None:
        raise RuntimeError

    monkeypatch.setattr(ir, "async_get", _raise)

    state = _collect_repairs_state(SimpleNamespace())

    assert state.available is False
    assert state.total == 0
    assert state.issues == []


@pytest.mark.asyncio
async def test_repairs_collector_updates_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """RepairsCollector stores collected state in the context."""
    from homeassistant.helpers import issue_registry as ir

    registry = SimpleNamespace(
        issues={
            ("demo", "warning"): _issue(
                domain="demo",
                issue_id="warning",
                severity="warning",
                is_fixable=True,
            )
        }
    )

    monkeypatch.setattr(ir, "async_get", lambda hass: registry)

    context = InspectionContext()
    collector = RepairsCollector()

    await collector.collect(SimpleNamespace(), context)

    assert context.repairs.available is True
    assert context.repairs.total == 1
    assert context.repairs.warning == 1
    assert context.repairs.fixable == 1
