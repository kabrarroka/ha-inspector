"""Entity inspection rules for HA Inspector."""

from __future__ import annotations

from ..context import InspectionContext
from ..models import Finding
from ..severity import Severity
from .base import BaseRule


class UnavailableEntitiesRule(BaseRule):
    """Detect an elevated number of unavailable entities."""

    rule_id = "UNAVAILABLE_ENTITIES"
    warning_percentage = 5.0
    error_percentage = 15.0

    async def check(self, context: InspectionContext) -> list[Finding]:
        """Check the percentage of unavailable entities."""
        entities = context.entities
        total = entities.get("total_entities", 0)
        unavailable = entities.get("unavailable_count", 0)

        if not isinstance(total, int) or total <= 0:
            return []
        if not isinstance(unavailable, int) or unavailable <= 0:
            return []

        percentage = round((unavailable / total) * 100, 2)

        if percentage >= self.error_percentage:
            severity = Severity.ERROR
            finding_id = "UNAVAILABLE_ENTITIES_EXCESSIVE"
            title = "Many entities are unavailable"
        elif percentage >= self.warning_percentage:
            severity = Severity.WARNING
            finding_id = "UNAVAILABLE_ENTITIES_HIGH"
            title = "Several entities are unavailable"
        else:
            return []

        return [
            Finding(
                finding_id=finding_id,
                severity=severity,
                title=title,
                description=(
                    f"{unavailable} of {total} entities are unavailable "
                    f"({percentage}%)."
                ),
                recommendation=(
                    "Review the affected domains and identify devices or "
                    "services that are disconnected, powered off or no longer in use."
                ),
                data={
                    "total_entities": total,
                    "unavailable_count": unavailable,
                    "unavailable_percentage": percentage,
                    "domains": entities.get("unavailable_domains", {}),
                },
            )
        ]


class UnknownEntitiesRule(BaseRule):
    """Detect an elevated number of entities with unknown state."""

    rule_id = "UNKNOWN_ENTITIES"
    warning_percentage = 5.0
    error_percentage = 15.0

    async def check(self, context: InspectionContext) -> list[Finding]:
        """Check the percentage of entities with unknown state."""
        entities = context.entities
        total = entities.get("total_entities", 0)
        unknown = entities.get("unknown_count", 0)

        if not isinstance(total, int) or total <= 0:
            return []
        if not isinstance(unknown, int) or unknown <= 0:
            return []

        percentage = round((unknown / total) * 100, 2)

        if percentage >= self.error_percentage:
            severity = Severity.ERROR
            finding_id = "UNKNOWN_ENTITIES_EXCESSIVE"
            title = "Many entities have an unknown state"
        elif percentage >= self.warning_percentage:
            severity = Severity.WARNING
            finding_id = "UNKNOWN_ENTITIES_HIGH"
            title = "Several entities have an unknown state"
        else:
            return []

        return [
            Finding(
                finding_id=finding_id,
                severity=severity,
                title=title,
                description=(
                    f"{unknown} of {total} entities have an unknown state "
                    f"({percentage}%)."
                ),
                recommendation=(
                    "Review template entities, helpers and integrations that may "
                    "not yet have received their first valid value."
                ),
                data={
                    "total_entities": total,
                    "unknown_count": unknown,
                    "unknown_percentage": percentage,
                    "domains": entities.get("unknown_domains", {}),
                },
            )
        ]


class DuplicateEntityNamesRule(BaseRule):
    """Detect friendly names shared by more than one entity."""

    rule_id = "DUPLICATE_ENTITY_NAMES"

    async def check(self, context: InspectionContext) -> list[Finding]:
        """Report duplicated entity names."""
        duplicates = context.entities.get("duplicate_names", [])
        if not isinstance(duplicates, list) or not duplicates:
            return []

        return [
            Finding(
                finding_id="DUPLICATE_ENTITY_NAMES_FOUND",
                severity=Severity.WARNING,
                title="Duplicate entity names detected",
                description=(
                    f"{len(duplicates)} friendly names are used by multiple entities."
                ),
                recommendation=(
                    "Give the affected entities distinct names so dashboards, "
                    "automations and voice commands are easier to understand."
                ),
                data={"duplicates": duplicates, "duplicate_count": len(duplicates)},
            )
        ]
