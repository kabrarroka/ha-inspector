"""Tests for persistent remediation baselines."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ha_inspector.engine.remediation_baselines import (
    RemediationBaselineStore,
)
from custom_components.ha_inspector.engine.remediation_plans import (
    RemediationPlan,
    RemediationStep,
)


def _plan(
    *,
    entity_id: str = "sensor.missing",
    action: str = "review_active_references",
    reference_count: int = 2,
) -> RemediationPlan:
    """Build a representative remediation plan."""
    return RemediationPlan(
        entity_id=entity_id,
        action=action,
        safety="review_required",
        reason="Entity is referenced by active configuration",
        reference_count=reference_count,
        active_reference_count=reference_count,
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


@pytest.mark.asyncio
async def test_load_empty_baselines() -> None:
    """Empty storage produces no remediation baselines."""
    store = RemediationBaselineStore(MagicMock())
    store._store.async_load = AsyncMock(return_value=None)

    await store.async_load()

    assert store.baselines() == {}


@pytest.mark.asyncio
async def test_set_baseline_persists_plan() -> None:
    """Setting a remediation baseline persists the complete plan."""
    store = RemediationBaselineStore(MagicMock())
    store._store.async_load = AsyncMock(return_value=None)
    store._store.async_save = AsyncMock()

    await store.async_load()

    plan = _plan()
    await store.async_set(plan)

    assert store.get(plan.entity_id) == plan
    assert store.baselines() == {
        plan.entity_id: plan,
    }

    store._store.async_save.assert_awaited_once_with(
        {
            "baselines": {
                "sensor.missing": {
                    "entity_id": "sensor.missing",
                    "action": "review_active_references",
                    "safety": "review_required",
                    "reason": "Entity is referenced by active configuration",
                    "reference_count": 2,
                    "active_reference_count": 2,
                    "disabled_reference_count": 0,
                    "steps": [
                        {
                            "configuration_type": "automation",
                            "configuration_id": "automation.example",
                            "status": "active",
                            "action": "review_entity_reference",
                        }
                    ],
                }
            }
        }
    )


@pytest.mark.asyncio
async def test_set_replaces_existing_entity_baseline() -> None:
    """A newer baseline replaces the previous plan for one entity."""
    store = RemediationBaselineStore(MagicMock())
    store._store.async_load = AsyncMock(return_value=None)
    store._store.async_save = AsyncMock()

    await store.async_load()

    await store.async_set(_plan(reference_count=2))
    replacement = _plan(reference_count=1)

    await store.async_set(replacement)

    assert store.get("sensor.missing") == replacement
    assert len(store.baselines()) == 1


@pytest.mark.asyncio
async def test_remove_baseline_persists_change() -> None:
    """Removing a baseline clears it from persistent state."""
    store = RemediationBaselineStore(MagicMock())
    store._store.async_load = AsyncMock(return_value=None)
    store._store.async_save = AsyncMock()

    await store.async_load()
    await store.async_set(_plan())

    store._store.async_save.reset_mock()

    await store.async_remove("sensor.missing")

    assert store.get("sensor.missing") is None
    assert store.baselines() == {}
    store._store.async_save.assert_awaited_once_with({"baselines": {}})


@pytest.mark.asyncio
async def test_load_restores_persisted_plan() -> None:
    """Persisted remediation plans are reconstructed on load."""
    store = RemediationBaselineStore(MagicMock())
    store._store.async_load = AsyncMock(
        return_value={
            "baselines": {
                "sensor.missing": {
                    "entity_id": "sensor.missing",
                    "action": "review_active_references",
                    "safety": "review_required",
                    "reason": "Entity is referenced by active configuration",
                    "reference_count": 2,
                    "active_reference_count": 2,
                    "disabled_reference_count": 0,
                    "steps": [
                        {
                            "configuration_type": "automation",
                            "configuration_id": "automation.example",
                            "status": "active",
                            "action": "review_entity_reference",
                        }
                    ],
                }
            }
        }
    )

    await store.async_load()

    assert store.get("sensor.missing") == _plan()


def test_baselines_returns_copy() -> None:
    """Returned baseline mappings cannot mutate internal state."""
    store = RemediationBaselineStore(MagicMock())

    store._baselines = {
        "sensor.missing": _plan(),
    }

    baselines = store.baselines()
    baselines.clear()

    assert store.get("sensor.missing") == _plan()


@pytest.mark.asyncio
async def test_load_ignores_invalid_storage_root() -> None:
    """Malformed storage root produces no remediation baselines."""
    store = RemediationBaselineStore(MagicMock())
    store._store.async_load = AsyncMock(return_value=["invalid"])

    await store.async_load()

    assert store.baselines() == {}


@pytest.mark.asyncio
async def test_load_ignores_invalid_baselines_container() -> None:
    """Malformed baselines container produces no remediation baselines."""
    store = RemediationBaselineStore(MagicMock())
    store._store.async_load = AsyncMock(
        return_value={
            "baselines": ["invalid"],
        }
    )

    await store.async_load()

    assert store.baselines() == {}


@pytest.mark.asyncio
async def test_load_skips_invalid_baseline_entries() -> None:
    """Invalid baseline entries do not prevent valid plans from loading."""
    store = RemediationBaselineStore(MagicMock())
    store._store.async_load = AsyncMock(
        return_value={
            "baselines": {
                "sensor.valid": {
                    "entity_id": "sensor.valid",
                    "action": "review_active_references",
                    "safety": "review_required",
                    "reason": "Entity is referenced by active configuration",
                    "reference_count": 1,
                    "active_reference_count": 1,
                    "disabled_reference_count": 0,
                    "steps": [
                        {
                            "configuration_type": "automation",
                            "configuration_id": "automation.example",
                            "status": "active",
                            "action": "review_entity_reference",
                        }
                    ],
                },
                "sensor.invalid": {
                    "entity_id": "sensor.invalid",
                    "action": "review_active_references",
                    "safety": "review_required",
                    "reason": "Entity is referenced by active configuration",
                    "reference_count": "invalid",
                    "active_reference_count": 1,
                    "disabled_reference_count": 0,
                    "steps": [],
                },
            }
        }
    )

    await store.async_load()

    assert store.baselines() == {
        "sensor.valid": _plan(
            entity_id="sensor.valid",
            reference_count=1,
        )
    }


@pytest.mark.asyncio
async def test_load_skips_mismatched_entity_key() -> None:
    """Stored entity key must match the serialized remediation plan."""
    store = RemediationBaselineStore(MagicMock())
    store._store.async_load = AsyncMock(
        return_value={
            "baselines": {
                "sensor.expected": {
                    "entity_id": "sensor.other",
                    "action": "review_active_references",
                    "safety": "review_required",
                    "reason": "Entity is referenced by active configuration",
                    "reference_count": 1,
                    "active_reference_count": 1,
                    "disabled_reference_count": 0,
                    "steps": [],
                }
            }
        }
    )

    await store.async_load()

    assert store.baselines() == {}


@pytest.mark.asyncio
async def test_load_skips_plan_with_invalid_step() -> None:
    """A malformed remediation step invalidates that stored plan."""
    store = RemediationBaselineStore(MagicMock())
    store._store.async_load = AsyncMock(
        return_value={
            "baselines": {
                "sensor.missing": {
                    "entity_id": "sensor.missing",
                    "action": "review_active_references",
                    "safety": "review_required",
                    "reason": "Entity is referenced by active configuration",
                    "reference_count": 1,
                    "active_reference_count": 1,
                    "disabled_reference_count": 0,
                    "steps": [
                        {
                            "configuration_type": "automation",
                            "configuration_id": 123,
                            "status": "active",
                            "action": "review_entity_reference",
                        }
                    ],
                }
            }
        }
    )

    await store.async_load()

    assert store.baselines() == {}


@pytest.mark.asyncio
async def test_load_skips_non_mapping_baseline_entry() -> None:
    """A non-mapping baseline entry is ignored."""
    store = RemediationBaselineStore(MagicMock())
    store._store.async_load = AsyncMock(
        return_value={
            "baselines": {
                "sensor.invalid": "invalid",
            }
        }
    )

    await store.async_load()

    assert store.baselines() == {}


@pytest.mark.asyncio
async def test_load_skips_plan_with_non_mapping_step() -> None:
    """A non-mapping remediation step invalidates that stored plan."""
    store = RemediationBaselineStore(MagicMock())
    store._store.async_load = AsyncMock(
        return_value={
            "baselines": {
                "sensor.missing": {
                    "entity_id": "sensor.missing",
                    "action": "review_active_references",
                    "safety": "review_required",
                    "reason": "Entity is referenced by active configuration",
                    "reference_count": 1,
                    "active_reference_count": 1,
                    "disabled_reference_count": 0,
                    "steps": ["invalid"],
                }
            }
        }
    )

    await store.async_load()

    assert store.baselines() == {}
