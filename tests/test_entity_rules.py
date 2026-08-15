"""Tests for HA Inspector entity and automation rules."""

from typing import cast

import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.entities_state import (
    DisabledAutomation,
    DuplicateEntityName,
    EntitiesState,
    EntitySummary,
)
from custom_components.ha_inspector.engine.rules.automations import (
    DisabledAutomationsRule,
)
from custom_components.ha_inspector.engine.rules.entities import (
    DuplicateEntityNamesRule,
    EntitiesWithoutAreaRule,
    UnavailableEntitiesRule,
    UnknownEntitiesRule,
)
from custom_components.ha_inspector.engine.severity import Severity


@pytest.mark.asyncio
async def test_duplicate_names_rule_returns_nothing_without_duplicates() -> None:
    context = InspectionContext(entities=EntitiesState())

    assert await DuplicateEntityNamesRule().check(context) == []


@pytest.mark.asyncio
async def test_duplicate_names_rule_reports_groups() -> None:
    context = InspectionContext(
        entities=EntitiesState(
            duplicate_names=[
                DuplicateEntityName(
                    name="Temperature",
                    entity_ids=[
                        "sensor.kitchen_temperature",
                        "sensor.living_room_temperature",
                    ],
                    count=2,
                )
            ],
            duplicate_name_count=1,
        )
    )

    findings = await DuplicateEntityNamesRule().check(context)

    assert len(findings) == 1
    assert findings[0].severity is Severity.WARNING
    assert findings[0].data["duplicate_count"] == 1


@pytest.mark.asyncio
async def test_disabled_automations_rule_returns_nothing_when_empty() -> None:
    context = InspectionContext(entities=EntitiesState())

    assert await DisabledAutomationsRule().check(context) == []


@pytest.mark.asyncio
async def test_disabled_automations_rule_reports_entries() -> None:
    context = InspectionContext(
        entities=EntitiesState(
            disabled_automations=[
                DisabledAutomation(
                    entity_id="automation.old_rule",
                    name="Old rule",
                    disabled_by="user",
                )
            ],
            disabled_automation_count=1,
        )
    )

    findings = await DisabledAutomationsRule().check(context)

    assert len(findings) == 1
    assert findings[0].severity is Severity.INFO
    assert findings[0].data["disabled_automation_count"] == 1

@pytest.mark.asyncio
async def test_unavailable_entities_rule_returns_nothing_without_entities() -> None:
    context = InspectionContext(
        entities=EntitiesState(
            total_entities=0,
            unavailable_count=0,
        )
    )

    assert await UnavailableEntitiesRule().check(context) == []


@pytest.mark.asyncio
async def test_unavailable_entities_rule_returns_nothing_below_threshold() -> None:
    context = InspectionContext(
        entities=EntitiesState(
            total_entities=100,
            unavailable_count=4,
        )
    )

    assert await UnavailableEntitiesRule().check(context) == []


@pytest.mark.asyncio
async def test_unavailable_entities_rule_warns_at_warning_threshold() -> None:
    context = InspectionContext(
        entities=EntitiesState(
            total_entities=100,
            unavailable_count=5,
            unavailable_domains={"sensor": 3, "light": 2},
        )
    )

    findings = await UnavailableEntitiesRule().check(context)

    assert len(findings) == 1

    finding = findings[0]

    assert finding.finding_id == "UNAVAILABLE_ENTITIES_HIGH"
    assert finding.severity is Severity.WARNING
    assert finding.data == {
        "total_entities": 100,
        "unavailable_count": 5,
        "unavailable_percentage": 5.0,
        "domains": {
            "sensor": 3,
            "light": 2,
        },
    }


@pytest.mark.asyncio
async def test_unavailable_entities_rule_errors_at_error_threshold() -> None:
    context = InspectionContext(
        entities=EntitiesState(
            total_entities=200,
            unavailable_count=30,
            unavailable_domains={"sensor": 30},
        )
    )

    findings = await UnavailableEntitiesRule().check(context)

    assert len(findings) == 1

    finding = findings[0]

    assert finding.finding_id == "UNAVAILABLE_ENTITIES_EXCESSIVE"
    assert finding.severity is Severity.ERROR
    assert finding.data["unavailable_percentage"] == 15.0


@pytest.mark.asyncio
async def test_unknown_entities_rule_returns_nothing_without_unknowns() -> None:
    context = InspectionContext(
        entities=EntitiesState(
            total_entities=100,
            unknown_count=0,
        )
    )

    assert await UnknownEntitiesRule().check(context) == []


@pytest.mark.asyncio
async def test_unknown_entities_rule_returns_nothing_below_threshold() -> None:
    context = InspectionContext(
        entities=EntitiesState(
            total_entities=100,
            unknown_count=4,
        )
    )

    assert await UnknownEntitiesRule().check(context) == []


@pytest.mark.asyncio
async def test_unknown_entities_rule_warns_at_warning_threshold() -> None:
    context = InspectionContext(
        entities=EntitiesState(
            total_entities=100,
            unknown_count=5,
            unknown_domains={"sensor": 5},
        )
    )

    findings = await UnknownEntitiesRule().check(context)

    assert len(findings) == 1

    finding = findings[0]

    assert finding.finding_id == "UNKNOWN_ENTITIES_HIGH"
    assert finding.severity is Severity.WARNING
    assert finding.data == {
        "total_entities": 100,
        "unknown_count": 5,
        "unknown_percentage": 5.0,
        "domains": {
            "sensor": 5,
        },
    }


@pytest.mark.asyncio
async def test_unknown_entities_rule_errors_at_error_threshold() -> None:
    context = InspectionContext(
        entities=EntitiesState(
            total_entities=200,
            unknown_count=30,
            unknown_domains={"sensor": 20, "binary_sensor": 10},
        )
    )

    findings = await UnknownEntitiesRule().check(context)

    assert len(findings) == 1

    finding = findings[0]

    assert finding.finding_id == "UNKNOWN_ENTITIES_EXCESSIVE"
    assert finding.severity is Severity.ERROR
    assert finding.data["unknown_percentage"] == 15.0

@pytest.mark.asyncio
async def test_entities_without_area_rule_returns_nothing_when_empty() -> None:
    context = InspectionContext(entities=EntitiesState())

    assert await EntitiesWithoutAreaRule().check(context) == []


@pytest.mark.asyncio
async def test_entities_without_area_rule_reports_entities() -> None:
    context = InspectionContext(
        entities=EntitiesState(
            unassigned_area_count=2,
            unassigned_area_entities=[
                EntitySummary(
                    entity_id="sensor.temperature",
                    name="Temperature",
                    domain="sensor",
                ),
                EntitySummary(
                    entity_id="light.garage",
                    name="Garage",
                    domain="light",
                ),
            ],
        )
    )

    findings = await EntitiesWithoutAreaRule().check(context)

    assert len(findings) == 1

    finding = findings[0]

    assert finding.finding_id == "ENTITIES_WITHOUT_AREA_FOUND"
    assert finding.severity is Severity.INFO
    assert finding.data["unassigned_area_count"] == 2
    assert [
        entity.entity_id for entity in finding.data["entities"]
    ] == [
        "sensor.temperature",
        "light.garage",
    ]

@pytest.mark.asyncio
async def test_unavailable_entities_rule_ignores_invalid_count() -> None:
    context = InspectionContext(
        entities=EntitiesState(
            total_entities=100,
            unavailable_count=cast(int, "invalid"),
        )
    )

    assert await UnavailableEntitiesRule().check(context) == []


@pytest.mark.asyncio
async def test_unknown_entities_rule_ignores_invalid_total() -> None:
    context = InspectionContext(
        entities=EntitiesState(
            total_entities=cast(int, "invalid"),
            unknown_count=5,
        )
    )

    assert await UnknownEntitiesRule().check(context) == []