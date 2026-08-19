"""Tests for Supervisor add-on health rules."""

import pytest

from custom_components.ha_inspector.engine.addons_state import AddonsState
from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.rules.addons import AddonHealthRule
from custom_components.ha_inspector.engine.severity import Severity


@pytest.mark.asyncio
async def test_addon_health_unavailable_returns_nothing() -> None:
    context = InspectionContext(
        addons=AddonsState(available=False)
    )

    assert await AddonHealthRule().check(context) == []


@pytest.mark.asyncio
async def test_addon_health_healthy_returns_nothing() -> None:
    context = InspectionContext(
        addons=AddonsState(
            available=True,
            total=2,
            started=1,
            stopped=1,
        )
    )

    assert await AddonHealthRule().check(context) == []


@pytest.mark.asyncio
async def test_addon_health_reports_error() -> None:
    context = InspectionContext(
        addons=AddonsState(
            available=True,
            total=1,
            error=1,
            problematic=[
                {
                    "slug": "broken",
                    "name": "Broken add-on",
                    "state": "error",
                }
            ],
        )
    )

    findings = await AddonHealthRule().check(context)

    assert len(findings) == 1
    assert findings[0].finding_id == "ADDON_STATE_ERROR"
    assert findings[0].severity is Severity.ERROR


@pytest.mark.asyncio
async def test_addon_health_reports_unknown() -> None:
    context = InspectionContext(
        addons=AddonsState(
            available=True,
            total=1,
            unknown=1,
            problematic=[
                {
                    "slug": "unknown",
                    "name": "Unknown add-on",
                    "state": "unknown",
                }
            ],
        )
    )

    findings = await AddonHealthRule().check(context)

    assert len(findings) == 1
    assert findings[0].finding_id == "ADDON_STATE_UNKNOWN"
    assert findings[0].severity is Severity.WARNING
