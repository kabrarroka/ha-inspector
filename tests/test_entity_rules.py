"""Tests for HA Inspector entity and automation rules."""

import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.rules.automations import (
    DisabledAutomationsRule,
)
from custom_components.ha_inspector.engine.rules.entities import (
    DuplicateEntityNamesRule,
)
from custom_components.ha_inspector.engine.severity import Severity


@pytest.mark.asyncio
async def test_duplicate_names_rule_returns_nothing_without_duplicates() -> None:
    context = InspectionContext(entities={"duplicate_names": []})
    assert await DuplicateEntityNamesRule().check(context) == []


@pytest.mark.asyncio
async def test_duplicate_names_rule_reports_groups() -> None:
    context = InspectionContext(
        entities={
            "duplicate_names": [
                {
                    "name": "Temperature",
                    "entity_ids": [
                        "sensor.kitchen_temperature",
                        "sensor.living_room_temperature",
                    ],
                    "count": 2,
                }
            ]
        }
    )

    findings = await DuplicateEntityNamesRule().check(context)

    assert len(findings) == 1
    assert findings[0].severity is Severity.WARNING
    assert findings[0].data["duplicate_count"] == 1


@pytest.mark.asyncio
async def test_disabled_automations_rule_returns_nothing_when_empty() -> None:
    context = InspectionContext(entities={"disabled_automations": []})
    assert await DisabledAutomationsRule().check(context) == []


@pytest.mark.asyncio
async def test_disabled_automations_rule_reports_entries() -> None:
    context = InspectionContext(
        entities={
            "disabled_automations": [
                {
                    "entity_id": "automation.old_rule",
                    "name": "Old rule",
                    "disabled_by": "user",
                }
            ]
        }
    )

    findings = await DisabledAutomationsRule().check(context)

    assert len(findings) == 1
    assert findings[0].severity is Severity.INFO
    assert findings[0].data["disabled_automation_count"] == 1
