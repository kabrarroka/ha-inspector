"""Tests for configuration reference classification helpers."""

from custom_components.ha_inspector.engine import (
    configuration_reference_classification as classification,
)


def test_classify_configuration_references_separates_active_and_disabled() -> None:
    assert classification.classify_configuration_references(
        [
            (
                "automation.active",
                ["light.kitchen", "sensor.temperature"],
                False,
            ),
            (
                "automation.disabled",
                ["light.kitchen", "switch.fan"],
                True,
            ),
        ],
        [
            (
                "script.active",
                ["light.kitchen"],
                False,
            )
        ],
        [
            (
                "scene.disabled",
                ["media_player.tv"],
                True,
            )
        ],
    ) == (
        classification.ConfigurationReferenceClassification(
            configuration_type="automation",
            active_configuration_count=1,
            disabled_configuration_count=1,
            active_reference_count=2,
            disabled_reference_count=2,
        ),
        classification.ConfigurationReferenceClassification(
            configuration_type="script",
            active_configuration_count=1,
            disabled_configuration_count=0,
            active_reference_count=1,
            disabled_reference_count=0,
        ),
        classification.ConfigurationReferenceClassification(
            configuration_type="scene",
            active_configuration_count=0,
            disabled_configuration_count=1,
            active_reference_count=0,
            disabled_reference_count=1,
        ),
    )


def test_classify_configuration_references_deduplicates_references() -> None:
    assert classification.classify_configuration_references(
        [
            (
                "automation.active",
                ["light.kitchen", "light.kitchen"],
                False,
            ),
            (
                "automation.active",
                ["light.kitchen"],
                False,
            ),
            (
                "automation.disabled",
                ["light.kitchen", "light.kitchen"],
                True,
            ),
        ],
        [],
        [],
    )[0] == classification.ConfigurationReferenceClassification(
        configuration_type="automation",
        active_configuration_count=1,
        disabled_configuration_count=1,
        active_reference_count=1,
        disabled_reference_count=1,
    )


def test_classify_configuration_references_handles_empty_input() -> None:
    assert classification.classify_configuration_references([], [], []) == (
        classification.ConfigurationReferenceClassification(
            configuration_type="automation",
            active_configuration_count=0,
            disabled_configuration_count=0,
            active_reference_count=0,
            disabled_reference_count=0,
        ),
        classification.ConfigurationReferenceClassification(
            configuration_type="script",
            active_configuration_count=0,
            disabled_configuration_count=0,
            active_reference_count=0,
            disabled_reference_count=0,
        ),
        classification.ConfigurationReferenceClassification(
            configuration_type="scene",
            active_configuration_count=0,
            disabled_configuration_count=0,
            active_reference_count=0,
            disabled_reference_count=0,
        ),
    )
