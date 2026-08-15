"""Tests for rule descriptor compatibility metadata."""

import pytest

from custom_components.ha_inspector.engine.category import Category
from custom_components.ha_inspector.engine.descriptors import RuleDescriptor
from custom_components.ha_inspector.engine.rules.base import (
    BaseRule,
    CompatibilityRuleDescriptor,
)
from custom_components.ha_inspector.engine.severity import Severity


def test_descriptor_id_alias_matches_rule_id() -> None:
    descriptor = CompatibilityRuleDescriptor(
        rule_id="entities.unavailable",
        title="Unavailable entities",
        category="entities",
        severity=Severity.WARNING,
    )

    assert descriptor.id == "entities.unavailable"


def test_descriptor_as_dict_is_stable_and_serializable() -> None:
    descriptor = CompatibilityRuleDescriptor(
        rule_id="recorder.keep_days",
        title="Recorder retention",
        category="recorder",
        severity=Severity.INFO,
        tags=("recorder", "storage"),
        weight=8,
        recommendation="Review recorder retention settings.",
    )

    assert descriptor.as_dict() == {
        "id": "recorder.keep_days",
        "rule_id": "recorder.keep_days",
        "title": "Recorder retention",
        "category": "recorder",
        "severity": Severity.INFO.label,
        "tags": ["recorder", "storage"],
        "weight": 8,
        "recommendation": "Review recorder retention settings.",
    }

def test_rule_descriptor_normalizes_category_and_serializes() -> None:
    descriptor = RuleDescriptor(
        rule_id="system.info",
        category=Category.SYSTEM,
        title="System information",
        description="General Home Assistant system information.",
        weight=10,
        tags=("system", "diagnostics"),
        enabled=False,
    )

    assert descriptor.category is Category.SYSTEM
    assert descriptor.as_dict() == {
        "id": "system.info",
        "category": Category.SYSTEM.value,
        "title": "System information",
        "description": "General Home Assistant system information.",
        "weight": 10,
        "tags": ["system", "diagnostics"],
        "enabled": False,
    }


@pytest.mark.parametrize(
    "rule_id",
    [
        "",
        "system",
    ],
)
def test_rule_descriptor_rejects_invalid_rule_id(rule_id: str) -> None:
    with pytest.raises(ValueError, match="dotted notation"):
        RuleDescriptor(
            rule_id=rule_id,
            category=Category.SYSTEM,
            title="System information",
            description="Description",
            weight=10,
        )


def test_rule_descriptor_rejects_unknown_category() -> None:
    with pytest.raises(ValueError, match="Unknown rule category"):
        RuleDescriptor(
            rule_id="system.info",
            category="not-a-category",  # type: ignore[arg-type]
            title="System information",
            description="Description",
            weight=10,
        )


@pytest.mark.parametrize(
    "weight",
    [
        -1,
        101,
    ],
)
def test_rule_descriptor_rejects_weight_outside_range(weight: int) -> None:
    with pytest.raises(ValueError, match="between 0 and 100"):
        RuleDescriptor(
            rule_id="system.info",
            category=Category.SYSTEM,
            title="System information",
            description="Description",
            weight=weight,
        )

@pytest.mark.parametrize(
    ("severity", "expected_icon"),
    [
        (Severity.INFO, "mdi:information-outline"),
        (Severity.WARNING, "mdi:alert-outline"),
        (Severity.ERROR, "mdi:alert-circle-outline"),
        (Severity.CRITICAL, "mdi:alert-octagon-outline"),
    ],
)
def test_severity_icons(
    severity: Severity,
    expected_icon: str,
) -> None:
    assert severity.icon == expected_icon

class NativeDescriptorRule(BaseRule):
    descriptor = RuleDescriptor(
        rule_id="test.native_descriptor",
        category=Category.SYSTEM,
        title="Native descriptor",
        description="Native descriptor test rule",
        weight=1,
        tags=("test",),
    )

    async def check(self, context):
        return []


class CatalogDescriptorRule(BaseRule):
    rule_id = "SYSTEM_INFORMATION"

    async def check(self, context):
        return []


def test_base_rule_metadata_returns_native_descriptor() -> None:
    rule = NativeDescriptorRule()

    assert rule.metadata is rule.descriptor


def test_base_rule_metadata_returns_catalog_descriptor() -> None:
    from custom_components.ha_inspector.engine.rules.catalog import (
        RULE_DESCRIPTORS,
    )

    rule = CatalogDescriptorRule()

    assert rule.metadata is RULE_DESCRIPTORS["SYSTEM_INFORMATION"]