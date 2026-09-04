"""Persistent remediation baselines for HA Inspector."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from homeassistant.helpers.storage import Store

from .remediation_plans import RemediationPlan, RemediationStep

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


_STORAGE_VERSION: Final = 1
_STORAGE_KEY: Final = "ha_inspector.remediation_baselines"


class RemediationBaselineStore:
    """Persist per-entity remediation baselines."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the remediation baseline store."""
        self._store = Store[dict[str, Any]](
            hass,
            _STORAGE_VERSION,
            _STORAGE_KEY,
        )
        self._baselines: dict[str, RemediationPlan] = {}

    async def async_load(self) -> None:
        """Load persisted remediation baselines."""
        data = await self._store.async_load()

        if not isinstance(data, dict):
            self._baselines = {}
            return

        stored_baselines = data.get("baselines")
        if not isinstance(stored_baselines, dict):
            self._baselines = {}
            return

        baselines: dict[str, RemediationPlan] = {}

        for entity_id, value in stored_baselines.items():
            if not isinstance(entity_id, str) or not isinstance(value, dict):
                continue

            plan = self._deserialize_plan(value)
            if plan is None or plan.entity_id != entity_id:
                continue

            baselines[entity_id] = plan

        self._baselines = baselines

    async def async_set(self, plan: RemediationPlan) -> None:
        """Set and persist the remediation baseline for one entity."""
        self._baselines[plan.entity_id] = plan
        await self._async_save()

    async def async_remove(self, entity_id: str) -> None:
        """Remove and persist the remediation baseline for one entity."""
        self._baselines.pop(entity_id, None)
        await self._async_save()

    def get(self, entity_id: str) -> RemediationPlan | None:
        """Return the remediation baseline for one entity."""
        return self._baselines.get(entity_id)

    def baselines(self) -> dict[str, RemediationPlan]:
        """Return a copy of all remediation baselines."""
        return dict(self._baselines)

    async def _async_save(self) -> None:
        """Persist current remediation baselines."""
        await self._store.async_save(
            {
                "baselines": {
                    entity_id: self._serialize_plan(plan)
                    for entity_id, plan in sorted(self._baselines.items())
                }
            }
        )

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
