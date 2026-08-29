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

    def __init__(
        self,
        *,
        warning_percentage: float = 5.0,
        error_percentage: float = 15.0,
    ) -> None:
        """Initialize configurable unavailable-entity thresholds."""
        warning_percentage = float(warning_percentage)
        error_percentage = float(error_percentage)

        if not 0.0 <= warning_percentage <= error_percentage <= 100.0:
            raise ValueError(
                "Unavailable entity thresholds must satisfy "
                "0 <= warning_percentage <= error_percentage <= 100"
            )

        self.warning_percentage = warning_percentage
        self.error_percentage = error_percentage

    async def check(self, context: InspectionContext) -> list[Finding]:
        """Check the percentage of unavailable entities."""
        entities = context.entities
        total = entities.total_entities
        unavailable = entities.unavailable_count

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
                    "domains": entities.unavailable_domains,
                },
            )
        ]


class UnknownEntitiesRule(BaseRule):
    """Detect an elevated number of entities with unknown state."""

    rule_id = "UNKNOWN_ENTITIES"
    warning_percentage = 5.0
    error_percentage = 15.0

    def __init__(
        self,
        *,
        warning_percentage: float = 5.0,
        error_percentage: float = 15.0,
    ) -> None:
        """Initialize configurable unknown-entity thresholds."""
        warning_percentage = float(warning_percentage)
        error_percentage = float(error_percentage)

        if not 0.0 <= warning_percentage <= error_percentage <= 100.0:
            raise ValueError(
                "Unknown entity thresholds must satisfy "
                "0 <= warning_percentage <= error_percentage <= 100"
            )

        self.warning_percentage = warning_percentage
        self.error_percentage = error_percentage

    async def check(self, context: InspectionContext) -> list[Finding]:
        """Check the percentage of entities with unknown state."""
        entities = context.entities
        total = entities.total_entities
        unknown = entities.unknown_count

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
                    "domains": entities.unknown_domains,
                },
            )
        ]


class DuplicateEntityNamesRule(BaseRule):
    """Detect friendly names shared by more than one entity."""

    rule_id = "DUPLICATE_ENTITY_NAMES"

    async def check(self, context: InspectionContext) -> list[Finding]:
        """Report duplicated entity names."""
        duplicates = context.entities.duplicate_names
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


class MissingEntityReferencesRule(BaseRule):
    """Report entity references that no longer resolve."""

    rule_id = "MISSING_ENTITY_REFERENCES"

    async def check(self, context: InspectionContext) -> list[Finding]:
        """Report known configuration references to missing entities."""
        entities = context.entities.missing_entities

        if not entities:
            return []

        return [
            Finding(
                finding_id="MISSING_ENTITY_REFERENCES_FOUND",
                severity=Severity.ERROR,
                title="Missing entity references detected",
                description=(
                    f"{len(entities)} referenced entities do not exist."
                ),
                recommendation=(
                    "Review the affected automations, scripts and scenes and "
                    "remove or replace references to entities that no longer exist."
                ),
                data={
                    "missing_entity_count": len(entities),
                    "missing_entities": entities,
                },
            )
        ]


class UnreferencedEntitiesRule(BaseRule):
    """Report entities with no known configuration references."""

    rule_id = "UNREFERENCED_ENTITIES"

    async def check(self, context: InspectionContext) -> list[Finding]:
        """Report entities not referenced by known dependency sources."""
        entities = context.entities.unreferenced_entities

        if not entities:
            return []

        return [
            Finding(
                finding_id="UNREFERENCED_ENTITIES_FOUND",
                severity=Severity.INFO,
                title="Entities with no known references detected",
                description=(
                    f"{len(entities)} entities have no references in the "
                    "configuration sources inspected by HA Inspector."
                ),
                recommendation=(
                    "Review these entities before removing them. They may still "
                    "be used by dashboards, integrations, external clients or "
                    "other sources that HA Inspector does not currently inspect."
                ),
                data={
                    "unreferenced_entity_count": len(entities),
                    "unreferenced_entities": entities,
                },
            )
        ]



class EntitiesWithoutAreaRule(BaseRule):
    """Report entities that are not assigned to an area."""

    rule_id = "ENTITIES_WITHOUT_AREA"

    async def check(self, context: InspectionContext) -> list[Finding]:
        """Report entities without an effective area assignment."""
        entities = context.entities.unassigned_area_entities

        if not entities:
            return []

        return [
            Finding(
                finding_id="ENTITIES_WITHOUT_AREA_FOUND",
                severity=Severity.INFO,
                title="Entities without an assigned area",
                description=(
                    f"{len(entities)} entities are not assigned to an area."
                ),
                recommendation=(
                    "Assign areas where appropriate to improve dashboards, "
                    "voice control and entity organization."
                ),
                data={
                    "unassigned_area_count": len(entities),
                    "entities": entities,
                },
            )
        ]
