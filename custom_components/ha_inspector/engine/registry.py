"""Component registry for the HA Inspector engine."""

from __future__ import annotations

from inspect import isabstract, isclass
from types import ModuleType

from .collectors.base import BaseCollector
from .discovery import DiscoveryError, discover_collectors, discover_rules
from .rules.base import BaseRule


class RegistryError(RuntimeError):
    """Raised when the engine registry cannot be built safely."""


class EngineRegistry:
    """Register, discover and instantiate collectors and rules."""

    def __init__(self) -> None:
        self._collector_types: dict[str, type[BaseCollector]] = {}
        self._rule_types: dict[str, type[BaseRule]] = {}

    @classmethod
    def discover(cls) -> "EngineRegistry":
        """Build a registry containing all built-in components."""
        registry = cls()
        try:
            for component in discover_collectors().values():
                registry.register_collector(component)
            for component in discover_rules().values():
                registry.register_rule(component)
        except DiscoveryError as err:
            raise RegistryError(str(err)) from err
        return registry

    def register_collector(self, collector_type: type[BaseCollector]) -> None:
        """Register a collector class."""
        identifier = getattr(collector_type, "collector_id", None)
        self._register(
            identifier=identifier,
            component_type=collector_type,
            target=self._collector_types,
        )

    def register_rule(self, rule_type: type[BaseRule]) -> None:
        """Register a rule class."""
        identifier = getattr(rule_type, "rule_id", None)
        self._register(
            identifier=identifier,
            component_type=rule_type,
            target=self._rule_types,
        )

    def _register_from_module(
        self,
        module: ModuleType,
        base_type: type[BaseCollector] | type[BaseRule],
    ) -> None:
        """Register concrete component classes declared by a module.

        Kept for compatibility with previous engine revisions and their tests.
        """
        for candidate in vars(module).values():
            if not isclass(candidate) or candidate is base_type:
                continue
            if not issubclass(candidate, base_type) or isabstract(candidate):
                continue
            if candidate.__module__ != module.__name__:
                continue

            if base_type is BaseCollector:
                self.register_collector(candidate)
            elif base_type is BaseRule:
                self.register_rule(candidate)
            else:
                raise RegistryError(f"Unsupported base type: {base_type.__name__}")

    @staticmethod
    def _register(
        *,
        identifier: object,
        component_type: type,
        target: dict[str, type],
    ) -> None:
        if not isinstance(identifier, str) or not identifier.strip():
            raise RegistryError(
                f"{component_type.__name__} does not define a valid identifier"
            )
        if identifier in target:
            previous = target[identifier]
            raise RegistryError(
                f"Duplicate identifier {identifier!r}: "
                f"{previous.__name__} and {component_type.__name__}"
            )
        target[identifier] = component_type

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
        """Compatibility accessor for registered collectors."""
        return self.create_collectors()

    @property
    def rules(self) -> list[BaseRule]:
        """Compatibility accessor for registered rules."""
        return self.create_rules()

    @property
    def collector_ids(self) -> tuple[str, ...]:
        """Return registered collector identifiers."""
        return tuple(sorted(self._collector_types))

    @property
    def rule_ids(self) -> tuple[str, ...]:
        """Return registered rule identifiers."""
        return tuple(sorted(self._rule_types))


InspectionRegistry = EngineRegistry

__all__ = [
    "EngineRegistry",
    "InspectionRegistry",
    "RegistryError",
]
