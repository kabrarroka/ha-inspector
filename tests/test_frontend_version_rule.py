"""Tests for the Home Assistant Frontend version rule."""

import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.rules.frontend_version import (
    FrontendVersionRule,
)
from custom_components.ha_inspector.engine.severity import Severity


@pytest.mark.asyncio
async def test_valid_frontend_version_has_no_findings() -> None:
    context = InspectionContext(
        system={"frontend_version": "20260624.5"}
    )

    findings = await FrontendVersionRule().check(context)

    assert findings == []


@pytest.mark.asyncio
@pytest.mark.parametrize("version", [None, "", "   "])
async def test_missing_frontend_version_has_no_findings(
    version: str | None,
) -> None:
    context = InspectionContext(system={"frontend_version": version})

    findings = await FrontendVersionRule().check(context)

    assert findings == []


@pytest.mark.asyncio
async def test_invalid_frontend_format_generates_warning() -> None:
    context = InspectionContext(
        system={"frontend_version": "not-a-version"}
    )

    findings = await FrontendVersionRule().check(context)

    assert len(findings) == 1
    assert findings[0].finding_id == "FRONTEND_VERSION_UNKNOWN"
    assert findings[0].severity is Severity.WARNING
    assert findings[0].title == "Unable to determine Frontend version"


@pytest.mark.asyncio
async def test_invalid_frontend_date_generates_warning() -> None:
    context = InspectionContext(
        system={"frontend_version": "20260230.1"}
    )

    findings = await FrontendVersionRule().check(context)

    assert len(findings) == 1
    assert findings[0].finding_id == "FRONTEND_VERSION_UNKNOWN"
