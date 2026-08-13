"""Tests for automatic rule discovery."""

from types import ModuleType, SimpleNamespace

import pytest

from custom_components.ha_inspector.engine.category import Category
from custom_components.ha_inspector.engine.context import InspectionContext
from custom_components.ha_inspector.engine.descriptors import RuleDescriptor
from custom_components.ha_inspector.engine.models import Finding
from custom_components.ha_inspector.engine.rules import discovery
from custom_components.ha_inspector.engine.rules.base import BaseRule


class AlphaRule(BaseRule):
    rule_id = "legacy.alpha"

    async def check(self, context: InspectionContext) -> list[Finding]:
        del context
        return []


class BetaRule(BaseRule):
    rule_id = "legacy.beta"

    async def check(self, context: InspectionContext) -> list[Finding]:
        del context
        return []


def _module_with(name: str, *classes: type) -> ModuleType:
    module = ModuleType(name)

    for candidate in classes:
        candidate.__module__ = module.__name__
        setattr(module, candidate.__name__, candidate)

    return module


def _descriptor(
    rule_id: str,
    *,
    enabled: bool = True,
) -> RuleDescriptor:
    return RuleDescriptor(
        rule_id=rule_id,
        category=Category.SYSTEM,
        title=rule_id,
        description=f"Descriptor for {rule_id}",
        weight=10,
        enabled=enabled,
    )


def test_iter_rule_modules_skips_internal_modules(monkeypatch) -> None:
    package = SimpleNamespace(
        __name__="custom_components.ha_inspector.engine.rules",
        __path__=["unused"],
    )

    module_infos = [
        SimpleNamespace(name=f"{package.__name__}.base"),
        SimpleNamespace(name=f"{package.__name__}.catalog"),
        SimpleNamespace(name=f"{package.__name__}.discovery"),
        SimpleNamespace(name=f"{package.__name__}._private"),
        SimpleNamespace(name=f"{package.__name__}.entities"),
        SimpleNamespace(name=f"{package.__name__}.system"),
    ]

    imported = {
        f"{package.__name__}.entities": ModuleType("entities"),
        f"{package.__name__}.system": ModuleType("system"),
    }

    monkeypatch.setattr(
        discovery.importlib,
        "import_module",
        lambda name: package if name == discovery.__package__ else imported[name],
    )
    monkeypatch.setattr(
        discovery.pkgutil,
        "iter_modules",
        lambda path, prefix: iter(module_infos),
    )

    modules = list(discovery._iter_rule_modules())

    assert modules == [
        imported[f"{package.__name__}.entities"],
        imported[f"{package.__name__}.system"],
    ]


def test_discover_rule_classes_returns_enabled_rules_sorted(monkeypatch) -> None:
    alpha_module = _module_with("tests.discovery_alpha", AlphaRule)
    beta_module = _module_with("tests.discovery_beta", BetaRule)

    monkeypatch.setattr(
        discovery,
        "_iter_rule_modules",
        lambda: iter((beta_module, alpha_module)),
    )
    monkeypatch.setattr(
        discovery,
        "RULE_DESCRIPTORS",
        {
            "legacy.alpha": _descriptor("system.alpha"),
            "legacy.beta": _descriptor("system.beta", enabled=False),
        },
    )

    rules = discovery.discover_rule_classes()

    assert rules == [AlphaRule]
    assert AlphaRule.descriptor.rule_id == "system.alpha"
    assert BetaRule.descriptor.rule_id == "system.beta"


def test_discover_rule_classes_rejects_missing_descriptor(monkeypatch) -> None:
    module = _module_with("tests.discovery_missing", AlphaRule)

    monkeypatch.setattr(
        discovery,
        "_iter_rule_modules",
        lambda: iter((module,)),
    )
    monkeypatch.setattr(
        discovery,
        "RULE_DESCRIPTORS",
        {},
    )

    with pytest.raises(
        ValueError,
        match="No RuleDescriptor registered for AlphaRule",
    ):
        discovery.discover_rule_classes()


def test_discover_rule_classes_rejects_duplicate_rule_ids(monkeypatch) -> None:
    alpha_module = _module_with("tests.discovery_duplicate_alpha", AlphaRule)
    beta_module = _module_with("tests.discovery_duplicate_beta", BetaRule)

    monkeypatch.setattr(
        discovery,
        "_iter_rule_modules",
        lambda: iter((alpha_module, beta_module)),
    )
    monkeypatch.setattr(
        discovery,
        "RULE_DESCRIPTORS",
        {
            "legacy.alpha": _descriptor("system.duplicate"),
            "legacy.beta": _descriptor("system.duplicate"),
        },
    )

    with pytest.raises(
        ValueError,
        match=r"Duplicate rule id 'system\.duplicate'",
    ):
        discovery.discover_rule_classes()

def test_discover_rule_classes_skips_invalid_candidates(monkeypatch) -> None:
    module = _module_with("tests.discovery_invalid", AlphaRule)

    module.BaseRule = BaseRule
    module.ForeignRule = BetaRule
    BetaRule.__module__ = "tests.somewhere_else"

    monkeypatch.setattr(
        discovery,
        "_iter_rule_modules",
        lambda: iter((module,)),
    )
    monkeypatch.setattr(
        discovery,
        "RULE_DESCRIPTORS",
        {
            "legacy.alpha": _descriptor("system.alpha"),
        },
    )

    rules = discovery.discover_rule_classes()

    assert rules == [AlphaRule]