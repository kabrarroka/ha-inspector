"""Public capability description for the HA Inspector engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .profiles import list_profiles
from .registry import EngineRegistry
from .request import InspectionRequest
from .rule_registry import RuleRegistry

CAPABILITIES_SCHEMA_VERSION = 1

REQUEST_FILTERS = (
    "include_rule_ids",
    "include_categories",
    "include_tags",
    "exclude_rule_ids",
    "exclude_categories",
    "exclude_tags",
)

REQUEST_OPTIONS = (
    "diagnostics",
)


@dataclass(frozen=True, slots=True)
class EngineCapabilities:
    """Describe the public capabilities of an engine registry."""

    schema_version: int
    collectors: tuple[str, ...]
    rules: tuple[dict[str, Any], ...]
    categories: tuple[str, ...]
    tags: tuple[str, ...]
    profiles: tuple[dict[str, str], ...]
    request_filters: tuple[str, ...]
    request_options: tuple[str, ...]

    @classmethod
    def from_registry(
        cls,
        registry: EngineRegistry,
    ) -> "EngineCapabilities":
        """Build capabilities from a discovered engine registry."""
        rule_registry = RuleRegistry(registry.create_rules())

        return cls(
            schema_version=CAPABILITIES_SCHEMA_VERSION,
            collectors=registry.collector_ids,
            rules=tuple(rule_registry.as_dicts()),
            categories=rule_registry.categories(),
            tags=rule_registry.tags(),
            profiles=tuple(
                profile.as_summary()
                for profile in list_profiles()
            ),
            request_filters=REQUEST_FILTERS,
            request_options=REQUEST_OPTIONS,
        )

    @property
    def rule_ids(self) -> tuple[str, ...]:
        """Return all registered rule identifiers."""
        return tuple(
            str(rule["rule_id"])
            for rule in self.rules
        )

    @property
    def profile_ids(self) -> tuple[str, ...]:
        """Return all available profile identifiers."""
        return tuple(
            profile["profile_id"]
            for profile in self.profiles
        )

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-safe capability document."""
        return {
            "schema_version": self.schema_version,
            "summary": {
                "collectors": len(self.collectors),
                "rules": len(self.rules),
                "categories": len(self.categories),
                "tags": len(self.tags),
                "profiles": len(self.profiles),
            },
            "collectors": list(self.collectors),
            "rules": [
                dict(rule)
                for rule in self.rules
            ],
            "rule_ids": list(self.rule_ids),
            "categories": list(self.categories),
            "tags": list(self.tags),
            "profiles": [
                dict(profile)
                for profile in self.profiles
            ],
            "profile_ids": list(self.profile_ids),
            "request": {
                "filters": list(self.request_filters),
                "options": list(self.request_options),
                "defaults": InspectionRequest().as_dict(),
            },
        }


def describe_engine(
    registry: EngineRegistry,
) -> dict[str, Any]:
    """Return the public capability document for an engine registry."""
    return EngineCapabilities.from_registry(registry).as_dict()


__all__ = [
    "CAPABILITIES_SCHEMA_VERSION",
    "EngineCapabilities",
    "REQUEST_FILTERS",
    "REQUEST_OPTIONS",
    "describe_engine",
]
