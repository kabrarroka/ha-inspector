import pytest

from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.integrations_state import (
    IntegrationsState,
    ProblematicIntegrationEntry,
)
from custom_components.ha_inspector.engine.rules.integrations import (
    IntegrationLifecycleErrorRule,
    IntegrationSetupErrorRule,
    IntegrationSetupRetryRule,
)
from custom_components.ha_inspector.engine.severity import Severity


@pytest.mark.asyncio
async def test_setup_error_rule_returns_nothing_without_matching_entries() -> None:
    context = InspectionContext(
        integrations=IntegrationsState(
            problematic_entries=[
                ProblematicIntegrationEntry(
                    domain="mqtt",
                    title="MQTT",
                    state="setup_retry",
                    reason="Connection failed",
                )
            ]
        )
    )

    assert await IntegrationSetupErrorRule().check(context) == []


@pytest.mark.asyncio
async def test_setup_error_rule_reports_matching_entries() -> None:
    entry = ProblematicIntegrationEntry(
        domain="tuya",
        title="Tuya",
        state="setup_error",
        reason="Authentication failed",
    )

    context = InspectionContext(
        integrations=IntegrationsState(
            problematic_entries=[entry]
        )
    )

    findings = await IntegrationSetupErrorRule().check(context)

    assert len(findings) == 1

    finding = findings[0]

    assert finding.finding_id == "INTEGRATION_SETUP_ERRORS"
    assert finding.severity is Severity.ERROR
    assert finding.data == {
        "count": 1,
        "entries": [entry],
    }


@pytest.mark.asyncio
async def test_setup_retry_rule_returns_nothing_without_matching_entries() -> None:
    context = InspectionContext(
        integrations=IntegrationsState(
            problematic_entries=[
                ProblematicIntegrationEntry(
                    domain="tuya",
                    title="Tuya",
                    state="setup_error",
                    reason="Authentication failed",
                )
            ]
        )
    )

    assert await IntegrationSetupRetryRule().check(context) == []


@pytest.mark.asyncio
async def test_setup_retry_rule_reports_matching_entries() -> None:
    entry = ProblematicIntegrationEntry(
        domain="mqtt",
        title="MQTT",
        state="setup_retry",
        reason="Broker unavailable",
    )

    context = InspectionContext(
        integrations=IntegrationsState(
            problematic_entries=[entry]
        )
    )

    findings = await IntegrationSetupRetryRule().check(context)

    assert len(findings) == 1

    finding = findings[0]

    assert finding.finding_id == "INTEGRATION_SETUP_RETRIES"
    assert finding.severity is Severity.WARNING
    assert finding.data == {
        "count": 1,
        "entries": [entry],
    }


@pytest.mark.asyncio
async def test_lifecycle_error_rule_returns_nothing_without_matching_entries() -> None:
    context = InspectionContext(
        integrations=IntegrationsState(
            problematic_entries=[
                ProblematicIntegrationEntry(
                    domain="mqtt",
                    title="MQTT",
                    state="setup_retry",
                    reason="Connection failed",
                )
            ]
        )
    )

    assert await IntegrationLifecycleErrorRule().check(context) == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "state",
    [
        "migration_error",
        "failed_unload",
    ],
)
async def test_lifecycle_error_rule_reports_matching_states(state: str) -> None:
    entry = ProblematicIntegrationEntry(
        domain="example",
        title="Example",
        state=state,
        reason="Lifecycle failure",
    )

    context = InspectionContext(
        integrations=IntegrationsState(
            problematic_entries=[entry]
        )
    )

    findings = await IntegrationLifecycleErrorRule().check(context)

    assert len(findings) == 1

    finding = findings[0]

    assert finding.finding_id == "INTEGRATION_LIFECYCLE_ERRORS"
    assert finding.severity is Severity.ERROR
    assert finding.data == {
        "count": 1,
        "entries": [entry],
    }