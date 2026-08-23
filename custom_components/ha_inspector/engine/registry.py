"""Automatic component registry for the HA Inspector engine."""

from __future__ import annotations

from collections.abc import Mapping
from importlib import import_module
from inspect import isabstract, isclass
from pkgutil import walk_packages
from types import ModuleType
from typing import Any, cast

from .collectors.base import BaseCollector
from .rules.base import BaseRule


class RegistryError(RuntimeError):
    """Raised when the engine registry cannot be built safely."""


class EngineRegistry:
    """Discover and instantiate collectors and rules automatically."""

    def __init__(self) -> None:
        self._collector_types: dict[str, type[BaseCollector]] = {}
        self._rule_types: dict[str, type[BaseRule]] = {}

    @classmethod
    def discover(cls) -> EngineRegistry:
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

    def create_rules(
        self,
        configuration: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> list[BaseRule]:
        """Return fresh rule instances in deterministic order."""
        configuration = configuration or {}

        unknown_rule_ids = set(configuration) - set(self._rule_types)
        if unknown_rule_ids:
            unknown = ", ".join(sorted(unknown_rule_ids))
            raise RegistryError(
                f"Configuration references unknown rules: {unknown}"
            )

        rules: list[BaseRule] = []

        for rule_id, rule_type in sorted(self._rule_types.items()):
            options = configuration.get(rule_id)

            if options is None:
                rules.append(rule_type())
                continue

            constructor = cast(Any, rule_type)
            rules.append(constructor(**dict(options)))

        return rules

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
        base_type: type[Any],
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
        base_type: type[Any],
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

                if not isinstance(identifier, str) or not identifier.strip():
                    raise RegistryError(
                        f"{candidate.__name__} does not define a valid identifier"
                    )

                if identifier in self._collector_types:
                    previous_collector = self._collector_types[identifier]
                    raise RegistryError(
                        f"Duplicate identifier {identifier!r}: "
                        f"{previous_collector.__name__} and {candidate.__name__}"
                    )

                self._collector_types[identifier] = cast(
                    type[BaseCollector],
                    candidate,
                )
            else:
                identifier = getattr(candidate, "rule_id", None)

                if not isinstance(identifier, str) or not identifier.strip():
                    raise RegistryError(
                        f"{candidate.__name__} does not define a valid identifier"
                    )

                if identifier in self._rule_types:
                    previous_rule = self._rule_types[identifier]
                    raise RegistryError(
                        f"Duplicate identifier {identifier!r}: "
                        f"{previous_rule.__name__} and {candidate.__name__}"
                    )

                self._rule_types[identifier] = cast(
                    type[BaseRule],
                    candidate,
                )


# Backward-compatible name used by previous engine revisions.
InspectionRegistry = EngineRegistry

__all__ = [
    "EngineRegistry",
    "InspectionRegistry",
    "RegistryError",
]
