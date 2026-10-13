"""Tests for the HA Inspector run service."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.ha_inspector import (
    SERVICE_RUN,
    SERVICE_RUN_SCHEMA,
    async_setup,
)
from custom_components.ha_inspector.const import (
    DATA_ACKNOWLEDGEMENTS,
    DATA_INSPECTION_HISTORY,
    DATA_REMEDIATION_STATE,
    DOMAIN,
)


@pytest.mark.asyncio
async def test_run_service_executes_inspection_with_profile() -> None:
    inspector = MagicMock()
    inspector.run = AsyncMock()

    result = MagicMock()
    result.metadata = {}
    result.as_dict.return_value = {
        "findings": [],
        "metadata": result.metadata,
    }

    inspector.run.return_value = result

    inspector_type = MagicMock(return_value=inspector)

    registry = MagicMock()
    registry.collector_ids = ("entities", "system")
    registry.rule_ids = ("CORE_VERSION", "UNAVAILABLE_ENTITIES")
    registry.create_collectors.return_value = ["collector"]
    registry.create_rules.return_value = ["rule"]

    hass = MagicMock()
    hass.data = {}
    hass.async_add_executor_job = AsyncMock(
        return_value=(inspector_type, registry)
    )

    await async_setup(hass, {})

    registrations = {
        call.args[1]: call.args[2]
        for call in hass.services.async_register.call_args_list
        if call.args[0] == DOMAIN
    }

    run_registration = next(
        call
        for call in hass.services.async_register.call_args_list
        if call.args[:2] == (DOMAIN, "run")
    )
    assert run_registration.kwargs["schema"] is SERVICE_RUN_SCHEMA

    service_call = MagicMock()
    service_call.data = {
        "profile": "quick",
    }

    response = await registrations["run"](service_call)

    inspector_type.assert_called_once_with(
        collectors=["collector"],
        rules=["rule"],
    )
    inspector.run.assert_awaited_once()

    assert result.metadata["registry"] == {
        "collectors": ["entities", "system"],
        "rules": ["CORE_VERSION", "UNAVAILABLE_ENTITIES"],
    }
    assert result.metadata["profile"] == "quick"

    from custom_components.ha_inspector.engine.inspection_scope import (
        inspection_scope,
    )

    request = inspector.run.await_args.kwargs["request"]
    assert result.metadata["inspection_scope"] == inspection_scope(request)

    assert response == {
        "findings": [],
        "metadata": result.metadata,
    }

def test_run_service_schema_rejects_unknown_fields() -> None:
    import voluptuous as vol

    with pytest.raises(vol.MultipleInvalid):
        SERVICE_RUN_SCHEMA({"unexpected": True})

@pytest.mark.asyncio
async def test_run_service_persists_inspection_history() -> None:
    """Run service stores a compact inspection history entry."""
    inspector = MagicMock()
    inspector.run = AsyncMock()

    result = MagicMock()
    result.metadata = {}
    result.remediation_progress = {
        "tracked_entities": 0,
        "pending": 0,
        "in_progress": 0,
        "resolved": 0,
        "total_actions": 0,
        "completed_actions": 0,
        "remaining_actions": 0,
        "new_references": 0,
        "entities": [],
    }
    result_data = {
        "findings": [],
        "metadata": result.metadata,
        "score": 100,
        "dashboard_summary": {
            "status": "excellent",
        },
    }
    result.as_dict.side_effect = lambda: {
        **result_data,
        "remediation_progress": result.remediation_progress,
        "remediation_trend": result.remediation_trend.as_dict(),
    }
    inspector.run.return_value = result

    inspector_type = MagicMock(return_value=inspector)

    registry = MagicMock()
    registry.collector_ids = ()
    registry.rule_ids = ()
    registry.create_collectors.return_value = []
    registry.create_rules.return_value = []

    history = MagicMock()
    history.async_add = AsyncMock()
    history.remediation_comparison_with.return_value = None

    from custom_components.ha_inspector.engine.remediation_trends import (
        remediation_lifecycle_trend,
    )

    expected_trend = remediation_lifecycle_trend([])
    history.remediation_trend_with.return_value = expected_trend

    hass = MagicMock()
    hass.data = {
        DOMAIN: {
            DATA_INSPECTION_HISTORY: history,
        }
    }
    hass.async_add_executor_job = AsyncMock(
        return_value=(inspector_type, registry)
    )

    await async_setup(hass, {})

    registrations = {
        call.args[1]: call.args[2]
        for call in hass.services.async_register.call_args_list
        if call.args[0] == DOMAIN
    }

    service_call = MagicMock()
    service_call.data = {}

    response = await registrations["run"](service_call)

    history.remediation_trend_with.assert_called_once()
    current_result = history.remediation_trend_with.call_args.args[0]
    assert current_result["remediation_progress"] == result.remediation_progress

    assert response["remediation_trend"] == expected_trend.as_dict()
    assert result.remediation_trend is expected_trend

    history.async_add.assert_awaited_once_with(response)
    assert history.remediation_trend_with.call_args.args[0] is not response

    assert response["metadata"] is result.metadata

    from custom_components.ha_inspector.engine.inspection_scope import (
        inspection_scope,
    )

    request = inspector.run.await_args.kwargs["request"]
    assert response["metadata"]["inspection_scope"] == inspection_scope(request)
    assert "profile" not in response["metadata"]
    assert current_result["metadata"]["inspection_scope"] == inspection_scope(request)


@pytest.mark.asyncio
async def test_run_service_applies_persisted_acknowledgements() -> None:
    """Run service converts persisted acknowledgements into suppression."""
    inspector = MagicMock()
    inspector.run = AsyncMock()

    result = MagicMock()
    result.metadata = {}
    result.as_dict.return_value = {
        "findings": [],
        "metadata": result.metadata,
    }
    inspector.run.return_value = result

    inspector_type = MagicMock(return_value=inspector)

    registry = MagicMock()
    registry.collector_ids = ()
    registry.rule_ids = ()
    registry.create_collectors.return_value = []
    registry.create_rules.return_value = []

    acknowledgements = MagicMock()
    acknowledgements.finding_ids = frozenset(
        {
            "UNAVAILABLE_ENTITIES_EXCESSIVE",
            "BACKUP_AGE_HIGH",
        }
    )

    hass = MagicMock()
    hass.data = {
        DOMAIN: {
            DATA_ACKNOWLEDGEMENTS: acknowledgements,
        }
    }
    hass.async_add_executor_job = AsyncMock(
        return_value=(inspector_type, registry)
    )

    await async_setup(hass, {})

    registrations = {
        call.args[1]: call.args[2]
        for call in hass.services.async_register.call_args_list
        if call.args[0] == DOMAIN
    }

    service_call = MagicMock()
    service_call.data = {}

    await registrations["run"](service_call)

    call = inspector.run.await_args

    assert call.args == (hass,)
    assert call.kwargs["request"] is not None

    suppression = call.kwargs["suppression"]

    assert suppression is not None
    assert suppression.finding_ids == frozenset(
        {
            "UNAVAILABLE_ENTITIES_EXCESSIVE",
            "BACKUP_AGE_HIGH",
        }
    )


@pytest.mark.asyncio
async def test_run_service_without_acknowledgement_store_uses_no_suppression() -> None:
    """Run service remains backward compatible without persisted state."""
    inspector = MagicMock()
    inspector.run = AsyncMock()

    result = MagicMock()
    result.metadata = {}
    result.as_dict.return_value = {
        "findings": [],
        "metadata": result.metadata,
    }
    inspector.run.return_value = result

    inspector_type = MagicMock(return_value=inspector)

    registry = MagicMock()
    registry.collector_ids = ()
    registry.rule_ids = ()
    registry.create_collectors.return_value = []
    registry.create_rules.return_value = []

    hass = MagicMock()
    hass.data = {}
    hass.async_add_executor_job = AsyncMock(
        return_value=(inspector_type, registry)
    )

    await async_setup(hass, {})

    registrations = {
        call.args[1]: call.args[2]
        for call in hass.services.async_register.call_args_list
        if call.args[0] == DOMAIN
    }

    service_call = MagicMock()
    service_call.data = {}

    await registrations["run"](service_call)

    assert inspector.run.await_args.kwargs["suppression"] is None


@pytest.mark.asyncio
async def test_run_service_captures_new_remediation_baselines() -> None:
    """Run service persists remediation baselines for newly affected entities."""
    from custom_components.ha_inspector.const import DATA_REMEDIATION_BASELINES
    from custom_components.ha_inspector.engine.remediation_plans import (
        RemediationPlan,
        RemediationStep,
    )

    registrations: dict[str, Any] = {}

    hass = MagicMock()
    hass.data = {}

    hass.services.async_register = MagicMock(
        side_effect=(
            lambda domain, service, handler, **kwargs:
            registrations.__setitem__(
                service,
                handler,
            )
        )
    )
    hass.async_add_executor_job = AsyncMock(
        return_value=(MagicMock(), MagicMock())
    )

    await async_setup(hass, {})

    plan = RemediationPlan(
        entity_id="sensor.missing",
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=1,
        active_reference_count=1,
        disabled_reference_count=0,
        steps=(
            RemediationStep(
                configuration_type="automation",
                configuration_id="automation.example",
                status="active",
                action="review_entity_reference",
            ),
        ),
    )

    inspector = MagicMock()
    result = MagicMock()
    result.metadata = {}
    result.remediation_plans = (plan,)
    result.as_dict.return_value = {
        "remediation_workflow": {
            "affected_entities": 1,
            "review_required": 1,
            "likely_safe": 0,
            "affected_configurations": 1,
            "removable_references": 0,
            "review_references": 1,
            "entities": [],
        }
    }

    inspector.run = AsyncMock(return_value=result)

    inspector_type = MagicMock(return_value=inspector)
    registry = MagicMock()
    registry.create_collectors.return_value = []
    registry.create_rules.return_value = []
    registry.collector_ids = ()
    registry.rule_ids = ()

    hass.async_add_executor_job = AsyncMock(
        return_value=(inspector_type, registry)
    )

    registrations.clear()
    await async_setup(hass, {})

    store = MagicMock()
    store.baselines.return_value = {}
    store.async_set = AsyncMock()
    hass.data.setdefault(DOMAIN, {})[
        DATA_REMEDIATION_BASELINES
    ] = store

    with patch(
        "custom_components.ha_inspector.engine.remediation_progress.build_remediation_progress"
    ) as build_progress:
        build_progress.return_value.progress = ()
        build_progress.return_value.new_baselines = (plan,)

        await registrations[SERVICE_RUN](MagicMock(data={}))

    assert build_progress.call_count == 2
    first_call, second_call = build_progress.call_args_list

    assert first_call.args[1] == (plan,)
    assert second_call.args == (
        {"sensor.missing": plan},
        (plan,),
    )

    store.baselines.assert_called_once_with()
    store.async_set.assert_awaited_once_with(plan)


@pytest.mark.asyncio
async def test_run_service_does_not_replace_existing_remediation_baseline() -> None:
    """Run service preserves an existing remediation baseline."""
    from custom_components.ha_inspector.const import DATA_REMEDIATION_BASELINES

    registrations: dict[str, Any] = {}

    inspector = MagicMock()
    result = MagicMock()
    result.metadata = {}
    result.as_dict.return_value = {}

    inspector.run = AsyncMock(return_value=result)

    inspector_type = MagicMock(return_value=inspector)
    registry = MagicMock()
    registry.create_collectors.return_value = []
    registry.create_rules.return_value = []
    registry.collector_ids = ()
    registry.rule_ids = ()

    hass = MagicMock()
    hass.data = {}
    hass.services.async_register = MagicMock(
        side_effect=(
            lambda domain, service, handler, **kwargs:
            registrations.__setitem__(
                service,
                handler,
            )
        )
    )
    hass.async_add_executor_job = AsyncMock(
        return_value=(inspector_type, registry)
    )

    await async_setup(hass, {})

    baseline = MagicMock()
    result.remediation_plans = (baseline,)

    store = MagicMock()
    store.baselines.return_value = {"sensor.missing": baseline}
    store.async_set = AsyncMock()
    hass.data.setdefault(DOMAIN, {})[
        DATA_REMEDIATION_BASELINES
    ] = store

    with patch(
        "custom_components.ha_inspector.engine.remediation_progress.build_remediation_progress"
    ) as build_progress:
        build_progress.return_value.progress = ()
        build_progress.return_value.new_baselines = ()

        await registrations[SERVICE_RUN](MagicMock(data={}))

    build_progress.assert_called_once_with(
        {"sensor.missing": baseline},
        (baseline,),
    )
    store.async_set.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_service_reports_resolved_remediation_baseline() -> None:
    """Run service reports a baseline as resolved when its plan disappears."""
    from custom_components.ha_inspector.const import DATA_REMEDIATION_BASELINES
    from custom_components.ha_inspector.engine.remediation_plans import (
        RemediationPlan,
        RemediationStep,
    )

    registrations: dict[str, Any] = {}

    inspector = MagicMock()
    result = MagicMock()
    result.metadata = {}
    result.remediation_plans = ()
    result.as_dict.side_effect = lambda: {
        "remediation_progress": result.remediation_progress,
        "resolved_remediation_items": result.resolved_remediation_items,
    }
    inspector.run = AsyncMock(return_value=result)

    inspector_type = MagicMock(return_value=inspector)
    registry = MagicMock()
    registry.create_collectors.return_value = []
    registry.create_rules.return_value = []
    registry.collector_ids = ()
    registry.rule_ids = ()

    hass = MagicMock()
    hass.data = {}
    hass.services.async_register = MagicMock(
        side_effect=(
            lambda domain, service, handler, **kwargs:
            registrations.__setitem__(
                service,
                handler,
            )
        )
    )
    hass.async_add_executor_job = AsyncMock(
        return_value=(inspector_type, registry)
    )

    await async_setup(hass, {})

    baseline = RemediationPlan(
        entity_id="sensor.missing",
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=1,
        active_reference_count=1,
        disabled_reference_count=0,
        steps=(
            RemediationStep(
                configuration_type="automation",
                configuration_id="automation.example",
                status="active",
                action="review_entity_reference",
            ),
        ),
    )

    store = MagicMock()
    store.baselines.return_value = {
        baseline.entity_id: baseline,
    }
    store.async_set = AsyncMock()

    hass.data.setdefault(DOMAIN, {})[
        DATA_REMEDIATION_BASELINES
    ] = store

    response = await registrations[SERVICE_RUN](MagicMock(data={}))

    assert response["remediation_progress"] == {
        "tracked_entities": 1,
        "pending": 0,
        "in_progress": 0,
        "resolved": 1,
        "total_actions": 1,
        "completed_actions": 1,
        "remaining_actions": 0,
        "new_references": 0,
        "entities": [
            {
                "entity_id": "sensor.missing",
                "status": "resolved",
                "total_action_count": 1,
                "completed_action_count": 1,
                "remaining_action_count": 0,
                "new_reference_count": 0,
            }
        ],
    }

    assert response["resolved_remediation_items"] == (
        {
            "entity_id": "sensor.missing",
            "completed_action_count": 1,
        },
    )

    store.async_set.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_service_reports_new_remediation_references() -> None:
    """Run service reports references introduced after the baseline."""
    from custom_components.ha_inspector.const import DATA_REMEDIATION_BASELINES
    from custom_components.ha_inspector.engine.remediation_plans import (
        RemediationPlan,
        RemediationStep,
    )

    registrations: dict[str, Any] = {}

    inspector = MagicMock()
    result = MagicMock()
    result.metadata = {}

    baseline = RemediationPlan(
        entity_id="sensor.missing",
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=1,
        active_reference_count=1,
        disabled_reference_count=0,
        steps=(
            RemediationStep(
                configuration_type="automation",
                configuration_id="automation.original",
                status="active",
                action="review_entity_reference",
            ),
        ),
    )
    current = RemediationPlan(
        entity_id="sensor.missing",
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=2,
        active_reference_count=2,
        disabled_reference_count=0,
        steps=(
            RemediationStep(
                configuration_type="automation",
                configuration_id="automation.original",
                status="active",
                action="review_entity_reference",
            ),
            RemediationStep(
                configuration_type="script",
                configuration_id="script.new_reference",
                status="active",
                action="review_entity_reference",
            ),
        ),
    )

    result.remediation_plans = (current,)
    result.as_dict.side_effect = lambda: {
        "remediation_progress": result.remediation_progress,
        "new_remediation_reference_items": (
            result.new_remediation_reference_items
        ),
    }
    inspector.run = AsyncMock(return_value=result)

    inspector_type = MagicMock(return_value=inspector)
    registry = MagicMock()
    registry.create_collectors.return_value = []
    registry.create_rules.return_value = []
    registry.collector_ids = ()
    registry.rule_ids = ()

    hass = MagicMock()
    hass.data = {}
    hass.services.async_register = MagicMock(
        side_effect=(
            lambda domain, service, handler, **kwargs:
            registrations.__setitem__(
                service,
                handler,
            )
        )
    )
    hass.async_add_executor_job = AsyncMock(
        return_value=(inspector_type, registry)
    )

    await async_setup(hass, {})

    store = MagicMock()
    store.baselines.return_value = {
        baseline.entity_id: baseline,
    }
    store.async_set = AsyncMock()

    hass.data.setdefault(DOMAIN, {})[
        DATA_REMEDIATION_BASELINES
    ] = store

    response = await registrations[SERVICE_RUN](MagicMock(data={}))

    assert response["remediation_progress"]["new_references"] == 1
    assert response["new_remediation_reference_items"] == (
        {
            "entity_id": "sensor.missing",
            "new_reference_count": 1,
        },
    )

    store.async_set.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_service_builds_remediation_lifecycle_summary() -> None:
    """Run service summarizes remediation lifecycle against prior history."""
    from custom_components.ha_inspector.const import (
        DATA_REMEDIATION_BASELINES,
    )
    from custom_components.ha_inspector.engine.historical_comparison import (
        HistoricalRemediationComparison,
    )
    from custom_components.ha_inspector.engine.remediation_plans import (
        RemediationProgress,
    )

    registrations: dict[str, Any] = {}

    inspector = MagicMock()
    result = MagicMock()
    result.metadata = {}
    result.remediation_plans = ()

    result.as_dict.side_effect = lambda: {
        "remediation_progress": result.remediation_progress,
        "resolved_remediation_items": result.resolved_remediation_items,
        "new_remediation_reference_items": (
            result.new_remediation_reference_items
        ),
        "remediation_lifecycle": result.remediation_lifecycle_summary,
    }

    inspector.run = AsyncMock(return_value=result)

    inspector_type = MagicMock(return_value=inspector)
    registry = MagicMock()
    registry.create_collectors.return_value = []
    registry.create_rules.return_value = []
    registry.collector_ids = ()
    registry.rule_ids = ()

    hass = MagicMock()
    hass.data = {}
    hass.services.async_register = MagicMock(
        side_effect=(
            lambda domain, service, handler, **kwargs:
            registrations.__setitem__(
                service,
                handler,
            )
        )
    )
    hass.async_add_executor_job = AsyncMock(
        return_value=(inspector_type, registry)
    )

    await async_setup(hass, {})

    store = MagicMock()
    store.baselines.return_value = {}
    store.async_set = AsyncMock()

    history = MagicMock()
    history.async_add = AsyncMock()
    history.remediation_comparison_with.return_value = HistoricalRemediationComparison(
        previous_tracked_entities=2,
        current_tracked_entities=2,
        tracked_entities_delta=0,
        previous_pending=2,
        current_pending=1,
        pending_delta=-1,
        previous_in_progress=0,
        current_in_progress=1,
        in_progress_delta=1,
        previous_resolved=0,
        current_resolved=0,
        resolved_delta=0,
        previous_completed_actions=0,
        current_completed_actions=1,
        completed_actions_delta=1,
        previous_remaining_actions=2,
        current_remaining_actions=1,
        remaining_actions_delta=-1,
        previous_new_references=0,
        current_new_references=0,
        new_references_delta=0,
    )

    domain_data = hass.data.setdefault(DOMAIN, {})
    domain_data[DATA_REMEDIATION_BASELINES] = store
    domain_data[DATA_INSPECTION_HISTORY] = history

    with patch(
        "custom_components.ha_inspector.engine."
        "remediation_progress.build_remediation_progress"
    ) as build_progress:
        build_progress.return_value.progress = (
            RemediationProgress(
                entity_id="sensor.missing",
                status="in_progress",
                total_action_count=2,
                completed_action_count=1,
                remaining_action_count=1,
                new_reference_count=0,
            ),
        )
        build_progress.return_value.new_baselines = ()

        response = await registrations[SERVICE_RUN](
            MagicMock(data={})
        )

    assert response["remediation_lifecycle"] == {
        "status": "progressing",
        "tracked_entities": 1,
        "pending": 0,
        "in_progress": 1,
        "resolved": 0,
        "completed_actions": 1,
        "remaining_actions": 1,
        "new_references": 0,
        "resolved_since_previous": 0,
        "newly_pending_since_previous": 0,
        "new_references_delta": 0,
    }

    history.remediation_comparison_with.assert_called_once()
    history.async_add.assert_awaited_once()



@pytest.mark.asyncio
async def test_run_service_persists_remediation_state() -> None:
    """Run service persists latest remediation progress and lifecycle."""
    inspector = MagicMock()
    inspector.run = AsyncMock()

    result = MagicMock()
    result.metadata = {}

    progress = {
        "tracked_entities": 1,
        "pending": 1,
        "in_progress": 0,
        "resolved": 0,
        "total_actions": 1,
        "completed_actions": 0,
        "remaining_actions": 1,
        "new_references": 0,
        "entities": [
            {
                "entity_id": "sensor.missing",
                "status": "pending",
                "total_action_count": 1,
                "completed_action_count": 0,
                "remaining_action_count": 1,
                "new_reference_count": 0,
            }
        ],
    }

    lifecycle = {
        "status": "active",
        "tracked_entities": 1,
        "pending": 1,
        "in_progress": 0,
        "resolved": 0,
        "completed_actions": 0,
        "remaining_actions": 1,
        "new_references": 0,
        "resolved_since_previous": 0,
        "newly_pending_since_previous": 0,
        "new_references_delta": 0,
    }

    result_data = {
        "findings": [],
        "metadata": result.metadata,
        "remediation_progress": progress,
        "remediation_lifecycle": lifecycle,
    }

    result.as_dict.return_value = result_data
    inspector.run.return_value = result

    inspector_type = MagicMock(return_value=inspector)

    registry = MagicMock()
    registry.collector_ids = ()
    registry.rule_ids = ()
    registry.create_collectors.return_value = []
    registry.create_rules.return_value = []

    remediation_state = MagicMock()
    remediation_state.async_set = AsyncMock()

    hass = MagicMock()
    hass.data = {
        DOMAIN: {
            DATA_REMEDIATION_STATE: remediation_state,
        }
    }
    hass.async_add_executor_job = AsyncMock(
        return_value=(inspector_type, registry)
    )

    await async_setup(hass, {})

    registrations = {
        call.args[1]: call.args[2]
        for call in hass.services.async_register.call_args_list
        if call.args[0] == DOMAIN
    }

    service_call = MagicMock()
    service_call.data = {}

    response = await registrations["run"](service_call)

    remediation_state.async_set.assert_awaited_once_with(
        {
            "progress": progress,
            "lifecycle": lifecycle,
        }
    )
    assert response is result_data


@pytest.mark.asyncio
async def test_run_service_exposes_existing_remediation_entity_summary() -> None:
    """Run service exposes persisted baseline age and remediation urgency."""
    from time import time

    from custom_components.ha_inspector.const import DATA_REMEDIATION_BASELINES
    from custom_components.ha_inspector.engine.remediation_baselines import (
        RemediationBaselineStore,
    )
    from custom_components.ha_inspector.engine.remediation_plans import (
        RemediationPlan,
        RemediationStep,
    )
    from custom_components.ha_inspector.engine.result import InspectionResult

    registrations: dict[str, Any] = {}

    hass = MagicMock()
    hass.data = {}
    hass.services.async_register = MagicMock(
        side_effect=lambda domain, service, handler, **kwargs: (
            registrations.__setitem__(service, handler)
        )
    )

    baseline = RemediationPlan(
        entity_id="sensor.missing",
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=1,
        active_reference_count=1,
        disabled_reference_count=0,
        steps=(
            RemediationStep(
                configuration_type="automation",
                configuration_id="automation.example",
                status="active",
                action="review_entity_reference",
            ),
        ),
    )

    store = RemediationBaselineStore(
        hass,
        clock=lambda: time() - 10 * 86400,
    )
    store._store.async_load = AsyncMock(return_value=None)
    store._store.async_save = AsyncMock()

    await store.async_load()
    await store.async_set(baseline)

    result = InspectionResult()
    result.remediation_plans = (baseline,)

    inspector = MagicMock()
    inspector.run = AsyncMock(return_value=result)

    inspector_type = MagicMock(return_value=inspector)

    registry = MagicMock()
    registry.create_collectors.return_value = []
    registry.create_rules.return_value = []
    registry.collector_ids = ()
    registry.rule_ids = ()

    hass.async_add_executor_job = AsyncMock(
        return_value=(inspector_type, registry)
    )

    await async_setup(hass, {})

    hass.data.setdefault(DOMAIN, {})[
        DATA_REMEDIATION_BASELINES
    ] = store

    response = await registrations[SERVICE_RUN](MagicMock(data={}))

    summaries = response["remediation_entity_summaries"]

    assert len(summaries) == 1

    summary = summaries[0]

    assert summary["entity_id"] == "sensor.missing"
    assert summary["status"] == "pending"
    assert summary["stalled"] is True
    assert summary["urgency"] == "medium"
    assert summary["new_reference_count"] == 0
    assert summary["total_action_count"] == 1
    assert summary["completed_action_count"] == 0
    assert summary["remaining_action_count"] == 1

    assert summary["age_seconds"] is not None
    assert 10 * 86400 <= summary["age_seconds"] < 10 * 86400 + 60


@pytest.mark.asyncio
async def test_run_service_exposes_new_remediation_entity_summary() -> None:
    """New remediation baselines receive an initial age and urgency."""
    from custom_components.ha_inspector.const import DATA_REMEDIATION_BASELINES
    from custom_components.ha_inspector.engine.remediation_baselines import (
        RemediationBaselineStore,
    )
    from custom_components.ha_inspector.engine.remediation_plans import (
        RemediationPlan,
        RemediationStep,
    )
    from custom_components.ha_inspector.engine.result import InspectionResult

    registrations: dict[str, Any] = {}

    hass = MagicMock()
    hass.data = {}
    hass.services.async_register = MagicMock(
        side_effect=lambda domain, service, handler, **kwargs: (
            registrations.__setitem__(service, handler)
        )
    )

    plan = RemediationPlan(
        entity_id="sensor.new",
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=1,
        active_reference_count=1,
        disabled_reference_count=0,
        steps=(
            RemediationStep(
                configuration_type="automation",
                configuration_id="automation.example",
                status="active",
                action="review_entity_reference",
            ),
        ),
    )

    store = RemediationBaselineStore(hass)
    store._store.async_load = AsyncMock(return_value=None)
    store._store.async_save = AsyncMock()

    await store.async_load()

    result = InspectionResult()
    result.remediation_plans = (plan,)

    inspector = MagicMock()
    inspector.run = AsyncMock(return_value=result)

    inspector_type = MagicMock(return_value=inspector)

    registry = MagicMock()
    registry.create_collectors.return_value = []
    registry.create_rules.return_value = []
    registry.collector_ids = ()
    registry.rule_ids = ()

    hass.async_add_executor_job = AsyncMock(
        return_value=(inspector_type, registry)
    )

    await async_setup(hass, {})

    hass.data.setdefault(DOMAIN, {})[
        DATA_REMEDIATION_BASELINES
    ] = store

    response = await registrations[SERVICE_RUN](MagicMock(data={}))

    summaries = response["remediation_entity_summaries"]

    assert len(summaries) == 1

    summary = summaries[0]

    assert summary["entity_id"] == "sensor.new"
    assert summary["status"] == "pending"
    assert summary["stalled"] is False
    assert summary["urgency"] == "low"
    assert summary["total_action_count"] == 1
    assert summary["completed_action_count"] == 0
    assert summary["remaining_action_count"] == 1
    assert summary["new_reference_count"] == 0

    assert summary["age_seconds"] is not None
    assert 0 <= summary["age_seconds"] < 60

    assert store.get("sensor.new") == plan
    store._store.async_save.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_service_exposes_resolved_remediation_entity_summary() -> None:
    """Resolved remediation retains baseline age without urgency."""
    from time import time

    from custom_components.ha_inspector.const import DATA_REMEDIATION_BASELINES
    from custom_components.ha_inspector.engine.remediation_baselines import (
        RemediationBaselineStore,
    )
    from custom_components.ha_inspector.engine.remediation_plans import (
        RemediationPlan,
        RemediationStep,
    )
    from custom_components.ha_inspector.engine.result import InspectionResult

    registrations: dict[str, Any] = {}

    hass = MagicMock()
    hass.data = {}
    hass.services.async_register = MagicMock(
        side_effect=lambda domain, service, handler, **kwargs: (
            registrations.__setitem__(service, handler)
        )
    )

    baseline = RemediationPlan(
        entity_id="sensor.resolved",
        action="review_active_references",
        safety="review_required",
        reason="Entity was referenced by active configuration",
        reference_count=1,
        active_reference_count=1,
        disabled_reference_count=0,
        steps=(
            RemediationStep(
                configuration_type="automation",
                configuration_id="automation.example",
                status="active",
                action="review_entity_reference",
            ),
        ),
    )

    store = RemediationBaselineStore(
        hass,
        clock=lambda: time() - 10 * 86400,
    )
    store._store.async_load = AsyncMock(return_value=None)
    store._store.async_save = AsyncMock()

    await store.async_load()
    await store.async_set(baseline)
    store._store.async_save.reset_mock()

    result = InspectionResult()
    result.remediation_plans = ()

    inspector = MagicMock()
    inspector.run = AsyncMock(return_value=result)

    inspector_type = MagicMock(return_value=inspector)

    registry = MagicMock()
    registry.create_collectors.return_value = []
    registry.create_rules.return_value = []
    registry.collector_ids = ()
    registry.rule_ids = ()

    hass.async_add_executor_job = AsyncMock(
        return_value=(inspector_type, registry)
    )

    await async_setup(hass, {})

    hass.data.setdefault(DOMAIN, {})[
        DATA_REMEDIATION_BASELINES
    ] = store

    response = await registrations[SERVICE_RUN](MagicMock(data={}))

    summaries = response["remediation_entity_summaries"]

    assert len(summaries) == 1

    summary = summaries[0]

    assert summary["entity_id"] == "sensor.resolved"
    assert summary["status"] == "resolved"
    assert summary["stalled"] is False
    assert summary["urgency"] == "none"
    assert summary["total_action_count"] == 1
    assert summary["completed_action_count"] == 1
    assert summary["remaining_action_count"] == 0
    assert summary["new_reference_count"] == 0

    assert summary["age_seconds"] is not None
    assert 10 * 86400 <= summary["age_seconds"] < 10 * 86400 + 60

    assert store.get("sensor.resolved") == baseline
    store._store.async_save.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_service_exposes_high_urgency_for_new_references() -> None:
    """Stalled remediation with new references has high urgency."""
    from time import time

    from custom_components.ha_inspector.const import DATA_REMEDIATION_BASELINES
    from custom_components.ha_inspector.engine.remediation_baselines import (
        RemediationBaselineStore,
    )
    from custom_components.ha_inspector.engine.remediation_plans import (
        RemediationPlan,
        RemediationStep,
    )
    from custom_components.ha_inspector.engine.result import InspectionResult

    registrations: dict[str, Any] = {}

    hass = MagicMock()
    hass.data = {}
    hass.services.async_register = MagicMock(
        side_effect=lambda domain, service, handler, **kwargs: (
            registrations.__setitem__(service, handler)
        )
    )

    baseline = RemediationPlan(
        entity_id="sensor.regressed",
        action="review_active_references",
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=1,
        active_reference_count=1,
        disabled_reference_count=0,
        steps=(
            RemediationStep(
                configuration_type="automation",
                configuration_id="automation.original",
                status="active",
                action="review_entity_reference",
            ),
        ),
    )

    current = RemediationPlan(
        entity_id="sensor.regressed",
        action="review_active_references",
        safety="review_required",
        reason="Entity has acquired another active reference",
        reference_count=2,
        active_reference_count=2,
        disabled_reference_count=0,
        steps=(
            RemediationStep(
                configuration_type="automation",
                configuration_id="automation.original",
                status="active",
                action="review_entity_reference",
            ),
            RemediationStep(
                configuration_type="script",
                configuration_id="script.new_reference",
                status="active",
                action="review_entity_reference",
            ),
        ),
    )

    store = RemediationBaselineStore(
        hass,
        clock=lambda: time() - 10 * 86400,
    )
    store._store.async_load = AsyncMock(return_value=None)
    store._store.async_save = AsyncMock()

    await store.async_load()
    await store.async_set(baseline)
    store._store.async_save.reset_mock()

    result = InspectionResult()
    result.remediation_plans = (current,)

    inspector = MagicMock()
    inspector.run = AsyncMock(return_value=result)

    inspector_type = MagicMock(return_value=inspector)

    registry = MagicMock()
    registry.create_collectors.return_value = []
    registry.create_rules.return_value = []
    registry.collector_ids = ()
    registry.rule_ids = ()

    hass.async_add_executor_job = AsyncMock(
        return_value=(inspector_type, registry)
    )

    await async_setup(hass, {})

    hass.data.setdefault(DOMAIN, {})[
        DATA_REMEDIATION_BASELINES
    ] = store

    response = await registrations[SERVICE_RUN](MagicMock(data={}))

    summaries = response["remediation_entity_summaries"]

    assert len(summaries) == 1

    summary = summaries[0]

    assert summary["entity_id"] == "sensor.regressed"
    assert summary["status"] == "in_progress"
    assert summary["stalled"] is True
    assert summary["urgency"] == "high"
    assert summary["new_reference_count"] == 1
    assert summary["total_action_count"] == 1
    assert summary["completed_action_count"] == 0
    assert summary["remaining_action_count"] == 1

    assert summary["age_seconds"] is not None
    assert 10 * 86400 <= summary["age_seconds"] < 10 * 86400 + 60

    assert store.get("sensor.regressed") == baseline
    store._store.async_save.assert_not_awaited()
