"""Tests for rule descriptor compatibility metadata."""

from custom_components.ha_inspector.engine.rules.base import (
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
