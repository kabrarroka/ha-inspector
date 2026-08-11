"""Automatic discovery of HA Inspector rules."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from collections.abc import Iterator
from types import ModuleType

from .base import BaseRule
from .catalog import RULE_DESCRIPTORS


def _iter_rule_modules() -> Iterator[ModuleType]:
    """Import every public module contained in the rules package."""
    package = importlib.import_module(__package__)
    prefix = f"{package.__name__}."

    for module_info in pkgutil.iter_modules(package.__path__, prefix):
        short_name = module_info.name.rsplit(".", 1)[-1]
        if short_name.startswith("_") or short_name in {
            "base",
            "catalog",
            "discovery",
        }:
            continue
        yield importlib.import_module(module_info.name)


def discover_rule_classes() -> list[type[BaseRule]]:
    """Discover, validate and return all enabled built-in rule classes."""
    discovered: dict[str, type[BaseRule]] = {}

    for module in _iter_rule_modules():
        for _, candidate in inspect.getmembers(module, inspect.isclass):
            if (
                candidate is BaseRule
                or not issubclass(candidate, BaseRule)
                or candidate.__module__ != module.__name__
                or inspect.isabstract(candidate)
            ):
                continue

            legacy_id = candidate.rule_id
            descriptor = RULE_DESCRIPTORS.get(legacy_id)
            if descriptor is None:
                raise ValueError(
                    f"No RuleDescriptor registered for {candidate.__name__} "
                    f"(legacy id: {legacy_id!r})"
                )
            if descriptor.rule_id in discovered:
                other = discovered[descriptor.rule_id]
                raise ValueError(
                    f"Duplicate rule id {descriptor.rule_id!r}: "
                    f"{other.__name__} and {candidate.__name__}"
                )

            candidate.descriptor = descriptor
            if descriptor.enabled:
                discovered[descriptor.rule_id] = candidate

    return [
        discovered[rule_id]
        for rule_id in sorted(discovered)
    ]
