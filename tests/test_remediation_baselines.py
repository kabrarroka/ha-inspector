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
    store = RemediationBaselineStore(
        MagicMock(),
        clock=lambda: 1234.0,
    )
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
                    "reason": (
                        "Entity is referenced by active configuration"
                    ),
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
            },
            "created_at": {
                "sensor.missing": 1234.0,
            },
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
    store = RemediationBaselineStore(
        MagicMock(),
        clock=lambda: 1234.0,
    )
    store._store.async_load = AsyncMock(return_value=None)
    store._store.async_save = AsyncMock()

    await store.async_load()
    await store.async_set(_plan())

    store._store.async_save.reset_mock()

    await store.async_remove("sensor.missing")

    assert store.get("sensor.missing") is None
    assert store.baselines() == {}
    assert store.created_at("sensor.missing") is None
    store._store.async_save.assert_awaited_once_with(
        {
            "baselines": {},
            "created_at": {},
        }
    )


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
                    "reason": (
                        "Entity is referenced by active configuration"
                    ),
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
            },
            "created_at": {
                "sensor.missing": 100.0,
            },
        }
    )
    store._store.async_save = AsyncMock()

    await store.async_load()

    assert store.get("sensor.missing") == _plan()
    assert store.created_at("sensor.missing") == 100.0
    store._store.async_save.assert_not_awaited()

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
                    "reason": (
                        "Entity is referenced by active configuration"
                    ),
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
                    "reason": (
                        "Entity is referenced by active configuration"
                    ),
                    "reference_count": "invalid",
                    "active_reference_count": 1,
                    "disabled_reference_count": 0,
                    "steps": [],
                },
            },
            "created_at": {
                "sensor.valid": 100.0,
            },
        }
    )
    store._store.async_save = AsyncMock()

    await store.async_load()

    assert store.baselines() == {
        "sensor.valid": _plan(
            entity_id="sensor.valid",
            reference_count=1,
        )
    }
    assert store.created_at("sensor.valid") == 100.0
    assert store.created_at("sensor.invalid") is None
    store._store.async_save.assert_not_awaited()

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


@pytest.mark.asyncio
async def test_new_baseline_records_creation_timestamp() -> None:
    """A new remediation baseline records its creation time."""
    store = RemediationBaselineStore(
        MagicMock(),
        clock=lambda: 200.0,
    )
    store._store.async_save = AsyncMock()

    plan = _plan()
    await store.async_set(plan)

    assert store.created_at(plan.entity_id) == 200.0


@pytest.mark.asyncio
async def test_replacing_baseline_preserves_creation_timestamp() -> None:
    """Replacing a baseline keeps its original creation time."""
    current_time = 200.0

    def clock() -> float:
        return current_time

    store = RemediationBaselineStore(MagicMock(), clock=clock)
    store._store.async_save = AsyncMock()

    await store.async_set(_plan(reference_count=2))

    current_time = 500.0
    await store.async_set(_plan(reference_count=1))

    assert store.created_at("sensor.missing") == 200.0


@pytest.mark.asyncio
async def test_remove_baseline_clears_creation_timestamp() -> None:
    """Removing a remediation baseline also removes its creation time."""
    store = RemediationBaselineStore(
        MagicMock(),
        clock=lambda: 200.0,
    )
    store._store.async_save = AsyncMock()

    await store.async_set(_plan())
    await store.async_remove("sensor.missing")

    assert store.created_at("sensor.missing") is None
    assert store.age_seconds("sensor.missing", now=500.0) is None


@pytest.mark.asyncio
async def test_legacy_baseline_load_assigns_creation_timestamp() -> None:
    """Legacy baselines receive and persist a migration timestamp."""
    store = RemediationBaselineStore(
        MagicMock(),
        clock=lambda: 300.0,
    )
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
    store._store.async_save = AsyncMock()

    await store.async_load()

    assert store.created_at("sensor.missing") == 300.0
    store._store.async_save.assert_awaited_once()


@pytest.mark.asyncio
async def test_invalid_creation_timestamp_is_repaired() -> None:
    """Invalid persisted timestamps are replaced during load."""
    store = RemediationBaselineStore(
        MagicMock(),
        clock=lambda: 400.0,
    )
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
                    "steps": [],
                }
            },
            "created_at": {
                "sensor.missing": "invalid",
            },
        }
    )
    store._store.async_save = AsyncMock()

    await store.async_load()

    assert store.created_at("sensor.missing") == 400.0
    store._store.async_save.assert_awaited_once()


def test_age_seconds_uses_persisted_creation_timestamp() -> None:
    """Remediation age is calculated from its persisted creation time."""
    store = RemediationBaselineStore(
        MagicMock(),
        clock=lambda: 250.0,
    )
    store._created_at = {
        "sensor.missing": 100.0,
    }

    assert store.age_seconds("sensor.missing") == 150.0
    assert store.age_seconds("sensor.missing", now=175.0) == 75.0


def test_age_seconds_never_returns_negative_age() -> None:
    """Clock regressions cannot produce negative remediation age."""
    store = RemediationBaselineStore(MagicMock())
    store._created_at = {
        "sensor.missing": 200.0,
    }

    assert store.age_seconds("sensor.missing", now=150.0) == 0.0


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (100, 100.0),
        (100.5, 100.5),
        (True, None),
        ("100", None),
        (-1, None),
        (float("nan"), None),
        (float("inf"), None),
        (float("-inf"), None),
    ],
)
def test_normalize_creation_timestamp(
    value: object,
    expected: float | None,
) -> None:
    """Persisted creation timestamps are normalized safely."""
    assert RemediationBaselineStore._normalize_timestamp(value) == expected


@pytest.mark.asyncio
async def test_legacy_baselines_share_migration_timestamp() -> None:
    """Legacy baselines loaded together share one migration timestamp."""
    clock_calls = 0

    def clock() -> float:
        nonlocal clock_calls
        clock_calls += 1
        return 500.0

    store = RemediationBaselineStore(MagicMock(), clock=clock)
    store._store.async_load = AsyncMock(
        return_value={
            "baselines": {
                "sensor.first": {
                    "entity_id": "sensor.first",
                    "action": "review_active_references",
                    "safety": "review_required",
                    "reason": "Entity is referenced by active configuration",
                    "reference_count": 1,
                    "active_reference_count": 1,
                    "disabled_reference_count": 0,
                    "steps": [],
                },
                "sensor.second": {
                    "entity_id": "sensor.second",
                    "action": "review_active_references",
                    "safety": "review_required",
                    "reason": "Entity is referenced by active configuration",
                    "reference_count": 1,
                    "active_reference_count": 1,
                    "disabled_reference_count": 0,
                    "steps": [],
                },
            }
        }
    )
    store._store.async_save = AsyncMock()

    await store.async_load()

    assert store.created_at("sensor.first") == 500.0
    assert store.created_at("sensor.second") == 500.0
    assert clock_calls == 1
    store._store.async_save.assert_awaited_once()
