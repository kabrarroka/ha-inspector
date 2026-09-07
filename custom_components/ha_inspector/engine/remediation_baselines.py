"""Persistent remediation baselines for HA Inspector."""

from __future__ import annotations

from collections.abc import Callable
from math import isfinite
from time import time
from typing import TYPE_CHECKING, Any, Final

from homeassistant.helpers.storage import Store

from .remediation_plans import RemediationPlan, RemediationStep

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


_STORAGE_VERSION: Final = 1
_STORAGE_KEY: Final = "ha_inspector.remediation_baselines"


class RemediationBaselineStore:
    """Persist per-entity remediation baselines."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        clock: Callable[[], float] = time,
    ) -> None:
        """Initialize the remediation baseline store."""
        self._store = Store[dict[str, Any]](
            hass,
            _STORAGE_VERSION,
            _STORAGE_KEY,
        )
        self._clock = clock
        self._baselines: dict[str, RemediationPlan] = {}
        self._created_at: dict[str, float] = {}

    async def async_load(self) -> None:
        """Load persisted remediation baselines."""
        data = await self._store.async_load()

        if not isinstance(data, dict):
            self._baselines = {}
            self._created_at = {}
            return

        stored_baselines = data.get("baselines")
        if not isinstance(stored_baselines, dict):
            self._baselines = {}
            self._created_at = {}
            return

        stored_created_at = data.get("created_at")
        if not isinstance(stored_created_at, dict):
            stored_created_at = {}

        baselines: dict[str, RemediationPlan] = {}
        created_at: dict[str, float] = {}
        migration_timestamp: float | None = None
        migration_needed = False

        for entity_id, value in stored_baselines.items():
            if not isinstance(entity_id, str) or not isinstance(value, dict):
                continue

            plan = self._deserialize_plan(value)
            if plan is None or plan.entity_id != entity_id:
                continue

            baselines[entity_id] = plan

            timestamp = self._normalize_timestamp(
                stored_created_at.get(entity_id)
            )

            if timestamp is None:
                if migration_timestamp is None:
                    migration_timestamp = float(self._clock())

                timestamp = migration_timestamp
                migration_needed = True

            created_at[entity_id] = timestamp

        self._baselines = baselines
        self._created_at = created_at

        if migration_needed:
            await self._async_save()

    async def async_set(self, plan: RemediationPlan) -> None:
        """Set and persist the remediation baseline for one entity."""
        self._baselines[plan.entity_id] = plan

        if plan.entity_id not in self._created_at:
            self._created_at[plan.entity_id] = float(self._clock())

        await self._async_save()

    async def async_remove(self, entity_id: str) -> None:
        """Remove and persist the remediation baseline for one entity."""
        self._baselines.pop(entity_id, None)
        self._created_at.pop(entity_id, None)
        await self._async_save()

    def get(self, entity_id: str) -> RemediationPlan | None:
        """Return the remediation baseline for one entity."""
        return self._baselines.get(entity_id)

    def baselines(self) -> dict[str, RemediationPlan]:
        """Return a copy of all remediation baselines."""
        return dict(self._baselines)

    def created_at(self, entity_id: str) -> float | None:
        """Return the creation timestamp for one remediation baseline."""
        return self._created_at.get(entity_id)

    def age_seconds(
        self,
        entity_id: str,
        *,
        now: float | None = None,
    ) -> float | None:
        """Return remediation baseline age in seconds."""
        created_at = self.created_at(entity_id)

        if created_at is None:
            return None

        current_time = float(self._clock()) if now is None else float(now)

        return max(0.0, current_time - created_at)

    async def _async_save(self) -> None:
        """Persist current remediation baselines."""
        await self._store.async_save(
            {
                "baselines": {
                    entity_id: self._serialize_plan(plan)
                    for entity_id, plan in sorted(self._baselines.items())
                },
                "created_at": {
                    entity_id: self._created_at[entity_id]
                    for entity_id in sorted(self._baselines)
                },
            }
        )

    @staticmethod
    def _normalize_timestamp(value: object) -> float | None:
        """Normalize a persisted Unix timestamp."""
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
        ):
            return None

        timestamp = float(value)

        if not isfinite(timestamp) or timestamp < 0:
            return None

        return timestamp

    @staticmethod
    def _serialize_plan(plan: RemediationPlan) -> dict[str, Any]:
        """Serialize a remediation plan for storage."""
        return {
            "entity_id": plan.entity_id,
            "action": plan.action,
            "safety": plan.safety,
            "reason": plan.reason,
            "reference_count": plan.reference_count,
            "active_reference_count": plan.active_reference_count,
            "disabled_reference_count": plan.disabled_reference_count,
            "steps": [
                {
                    "configuration_type": step.configuration_type,
                    "configuration_id": step.configuration_id,
                    "status": step.status,
                    "action": step.action,
                }
                for step in plan.steps
            ],
        }

    @staticmethod
    def _deserialize_plan(data: dict[str, Any]) -> RemediationPlan | None:
        """Deserialize a stored remediation plan."""
        entity_id = data.get("entity_id")
        action = data.get("action")
        safety = data.get("safety")
        reason = data.get("reason")
        reference_count = data.get("reference_count")
        active_reference_count = data.get("active_reference_count")
        disabled_reference_count = data.get("disabled_reference_count")
        stored_steps = data.get("steps")

        if (
            not isinstance(entity_id, str)
            or not isinstance(action, str)
            or not isinstance(safety, str)
            or not isinstance(reason, str)
            or not isinstance(reference_count, int)
            or not isinstance(active_reference_count, int)
            or not isinstance(disabled_reference_count, int)
            or not isinstance(stored_steps, list)
        ):
            return None

        steps: list[RemediationStep] = []

        for stored_step in stored_steps:
            if not isinstance(stored_step, dict):
                return None

            configuration_type = stored_step.get("configuration_type")
            configuration_id = stored_step.get("configuration_id")
            status = stored_step.get("status")
            step_action = stored_step.get("action")

            if (
                not isinstance(configuration_type, str)
                or not isinstance(configuration_id, str)
                or not isinstance(status, str)
                or not isinstance(step_action, str)
            ):
                return None

            steps.append(
                RemediationStep(
                    configuration_type=configuration_type,
                    configuration_id=configuration_id,
                    status=status,
                    action=step_action,
                )
            )

        return RemediationPlan(
            entity_id=entity_id,
            action=action,
            safety=safety,
            reason=reason,
            reference_count=reference_count,
            active_reference_count=active_reference_count,
            disabled_reference_count=disabled_reference_count,
            steps=tuple(steps),
        )


__all__ = ["RemediationBaselineStore"]
