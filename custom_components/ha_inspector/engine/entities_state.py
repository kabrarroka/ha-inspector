"""Typed entity state model for HA Inspector."""

from __future__ import annotations

from dataclasses import dataclass, field

from .base_state import BaseState


@dataclass(slots=True)
class EntitySummary:
    """Represent a compact entity description."""

    entity_id: str
    name: str
    domain: str


@dataclass(slots=True)
class DuplicateEntityName:
    """Represent a duplicated friendly name."""

    name: str
    entity_ids: list[str] = field(default_factory=list)
    count: int = 0


@dataclass(slots=True)
class DisabledAutomation:
    """Represent a disabled automation registry entry."""

    entity_id: str
    name: str
    disabled_by: str

@dataclass(slots=True)
class AutomationDependencySummary:
    """Represent resolved entity dependencies for one automation."""

    entity_id: str
    name: str
    referenced_entities: list[str] = field(default_factory=list)
    referenced_entity_count: int = 0

@dataclass(slots=True)
class ScriptDependencySummary:
    """Represent resolved entity dependencies for one script."""

    entity_id: str
    name: str
    referenced_entities: list[str] = field(default_factory=list)
    referenced_entity_count: int = 0


@dataclass(slots=True)
class SceneDependencySummary:
    """Represent resolved entity dependencies for one scene."""

    entity_id: str
    name: str
    referenced_entities: list[str] = field(default_factory=list)
    referenced_entity_count: int = 0


@dataclass(slots=True)
class EntitiesState(BaseState):
    """Represent the stable entity inspection contract."""

    total_entities: int = 0
    domain_counts: dict[str, int] = field(default_factory=dict)

    unavailable_count: int = 0
    unknown_count: int = 0

    unavailable_domains: dict[str, int] = field(default_factory=dict)
    unknown_domains: dict[str, int] = field(default_factory=dict)

    unavailable_entities: list[EntitySummary] = field(default_factory=list)
    unknown_entities: list[EntitySummary] = field(default_factory=list)

    duplicate_name_count: int = 0
    duplicate_names: list[DuplicateEntityName] = field(default_factory=list)

    disabled_automation_count: int = 0
    disabled_automations: list[DisabledAutomation] = field(default_factory=list)

    automation_dependency_count: int = 0
    automation_dependencies: list[AutomationDependencySummary] = field(
        default_factory=list
    )

    script_dependency_count: int = 0
    script_dependencies: list[ScriptDependencySummary] = field(
        default_factory=list
    )

    scene_dependency_count: int = 0
    scene_dependencies: list[SceneDependencySummary] = field(
        default_factory=list
    )

    unassigned_area_count: int = 0
    unassigned_area_entities: list[EntitySummary] = field(default_factory=list)
