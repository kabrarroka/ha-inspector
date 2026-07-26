"""Automatic discovery of HA Inspector engine components."""

from __future__ import annotations

from importlib import import_module
from inspect import isabstract, isclass
from pkgutil import walk_packages
from types import ModuleType
from typing import Generic, TypeVar

from .collectors.base import BaseCollector
from .rules.base import BaseRule

ComponentT = TypeVar("ComponentT", BaseCollector, BaseRule)


class DiscoveryError(RuntimeError):
    """Raised when automatic component discovery fails."""


class Discovery(Generic[ComponentT]):
    """Discover concrete subclasses declared inside a Python package."""

    def __init__(
        self,
        package_name: str,
        base_type: type[ComponentT],
        identifier_attribute: str,
    ) -> None:
        self.package_name = package_name
        self.base_type = base_type
        self.identifier_attribute = identifier_attribute

    def discover(self) -> dict[str, type[ComponentT]]:
        """Return discovered component classes indexed by identifier."""
        discovered: dict[str, type[ComponentT]] = {}
        package = import_module(self.package_name)
        self._discover_module(package, discovered)

        package_path = getattr(package, "__path__", None)
        if package_path is None:
            return discovered

        for module_info in walk_packages(
            package_path,
            f"{self.package_name}.",
        ):
            if module_info.name.rsplit(".", 1)[-1] == "base":
                continue
            module = import_module(module_info.name)
            self._discover_module(module, discovered)

        return discovered

    def _discover_module(
        self,
        module: ModuleType,
        discovered: dict[str, type[ComponentT]],
    ) -> None:
        for candidate in vars(module).values():
            if not isclass(candidate) or candidate is self.base_type:
                continue
            if not issubclass(candidate, self.base_type) or isabstract(candidate):
                continue
            if candidate.__module__ != module.__name__:
                continue

            identifier = getattr(candidate, self.identifier_attribute, None)
            if not isinstance(identifier, str) or not identifier.strip():
                raise DiscoveryError(
                    f"{candidate.__name__} does not define a valid "
                    f"{self.identifier_attribute}"
                )

            if identifier in discovered:
                previous = discovered[identifier]
                raise DiscoveryError(
                    f"Duplicate identifier {identifier!r}: "
                    f"{previous.__name__} and {candidate.__name__}"
                )

            discovered[identifier] = candidate


def discover_collectors() -> dict[str, type[BaseCollector]]:
    """Discover all built-in collectors."""
    return Discovery(
        "custom_components.ha_inspector.engine.collectors",
        BaseCollector,
        "collector_id",
    ).discover()


def discover_rules() -> dict[str, type[BaseRule]]:
    """Discover all built-in rules."""
    return Discovery(
        "custom_components.ha_inspector.engine.rules",
        BaseRule,
        "rule_id",
    ).discover()
