"""Automatic component registry for the HA Inspector engine."""

from __future__ import annotations

from importlib import import_module
from inspect import isabstract, isclass
from pkgutil import walk_packages
from types import ModuleType
from typing import TypeVar

from .collectors.base import BaseCollector
from .rules.base import BaseRule

RegistryItem = TypeVar("RegistryItem", BaseCollector, BaseRule)


class RegistryError(RuntimeError):
    """Raised when the engine registry cannot be built safely."""


class EngineRegistry:
    """Discover and instantiate collectors and rules automatically."""

    def __init__(self) -> None:
        self._collector_types: dict[str, type[BaseCollector]] = {}
        self._rule_types: dict[str, type[BaseRule]] = {}

    @classmethod
    def discover(cls) -> "EngineRegistry":
        """Build a registry by scanning the collectors and rules packages."""
        registry = cls()
        registry._discover_package(
            "custom_components.ha_inspector.engine.collectors",
            BaseCollector,
        )
        registry._discover_package(
            "custom_components.ha_inspector.engine.rules",
            BaseRule,
        )
        return registry

    def create_collectors(self) -> list[BaseCollector]:
        """Return fresh collector instances in deterministic order."""
        return [
            collector_type()
            for _, collector_type in sorted(self._collector_types.items())
        ]

    def create_rules(self) -> list[BaseRule]:
        """Return fresh rule instances in deterministic order."""
        return [
            rule_type()
            for _, rule_type in sorted(self._rule_types.items())
        ]

    @property
    def collectors(self) -> list[BaseCollector]:
        """Compatibility accessor for discovered collectors."""
        return self.create_collectors()

    @property
    def rules(self) -> list[BaseRule]:
        """Compatibility accessor for discovered rules."""
        return self.create_rules()

    @property
    def collector_ids(self) -> tuple[str, ...]:
        """Return registered collector identifiers."""
        return tuple(sorted(self._collector_types))

    @property
    def rule_ids(self) -> tuple[str, ...]:
        """Return registered rule identifiers."""
        return tuple(sorted(self._rule_types))

    def _discover_package(
        self,
        package_name: str,
        base_type: type[RegistryItem],
    ) -> None:
        package = import_module(package_name)
        self._register_from_module(package, base_type)

        package_path = getattr(package, "__path__", None)
        if package_path is None:
            return

        for module_info in walk_packages(
            package_path,
            f"{package_name}.",
        ):
            if module_info.name.rsplit(".", 1)[-1] == "base":
                continue

            module = import_module(module_info.name)
            self._register_from_module(module, base_type)

    def _register_from_module(
        self,
        module: ModuleType,
        base_type: type[RegistryItem],
    ) -> None:
        for candidate in vars(module).values():
            if not isclass(candidate) or candidate is base_type:
                continue
            if not issubclass(candidate, base_type) or isabstract(candidate):
                continue
            if candidate.__module__ != module.__name__:
                continue

            if base_type is BaseCollector:
                identifier = getattr(candidate, "collector_id", None)
                target = self._collector_types
            else:
                identifier = getattr(candidate, "rule_id", None)
                target = self._rule_types

            if not isinstance(identifier, str) or not identifier.strip():
                raise RegistryError(
                    f"{candidate.__name__} does not define a valid identifier"
                )

            if identifier in target:
                previous = target[identifier]
                raise RegistryError(
                    f"Duplicate identifier {identifier!r}: "
                    f"{previous.__name__} and {candidate.__name__}"
                )

            target[identifier] = candidate


# Backward-compatible name used by previous engine revisions.
InspectionRegistry = EngineRegistry

__all__ = [
    "EngineRegistry",
    "InspectionRegistry",
    "RegistryError",
]
