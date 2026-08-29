"""Tests for HA Inspector localization helpers."""

from __future__ import annotations

from custom_components.ha_inspector.engine.i18n import (
    normalize_language,
    translate,
)


def test_normalize_language() -> None:
    assert normalize_language(None) == "en"
    assert normalize_language("") == "en"
    assert normalize_language("es") == "es"
    assert normalize_language("es-ES") == "es"
    assert normalize_language("ES_es") == "es"
    assert normalize_language("en-US") == "en"
    assert normalize_language("de-DE") == "en"


def test_translate_english() -> None:
    assert (
        translate(
            "backup_age.too_old.title",
            language="en",
        )
        == "The newest backup is too old"
    )


def test_translate_spanish() -> None:
    assert (
        translate(
            "backup_age.too_old.title",
            language="es",
        )
        == "La copia de seguridad más reciente es demasiado antigua"
    )


def test_translate_with_variables() -> None:
    assert (
        translate(
            "backup_age.description",
            language="es",
            variables={"age_days": 12},
        )
        == "La copia de seguridad más reciente de Home Assistant tiene 12 días."
    )


def test_translate_falls_back_to_english() -> None:
    assert (
        translate(
            "backup_age.recommendation",
            language="de",
        )
        == (
            "Create a new backup and verify that scheduled backups "
            "are running correctly."
        )
    )


def test_translate_unknown_key_returns_key() -> None:
    assert translate("missing.key", language="es") == "missing.key"


def test_localize_finding_preserves_technical_data() -> None:
    from custom_components.ha_inspector.engine.i18n import localize_finding
    from custom_components.ha_inspector.engine.models import Finding
    from custom_components.ha_inspector.engine.severity import Severity

    finding = Finding(
        finding_id="DISK_FREE_SPACE_LOW",
        severity=Severity.WARNING,
        title="Disk free space is low",
        description="English description",
        recommendation="English recommendation",
        data={"free_percent": 12.5},
    )

    localized = localize_finding(finding, "es")

    assert localized.finding_id == finding.finding_id
    assert localized.severity == finding.severity
    assert localized.data == finding.data
    assert localized.title == "El espacio libre en disco es bajo"
    assert "12.50%" in localized.description
    assert localized.recommendation is not None
    assert "almacenamiento" in localized.recommendation

def test_all_findings_have_spanish_translation() -> None:
    """Ensure every statically declared finding has a Spanish translation."""
    import ast
    from pathlib import Path

    from custom_components.ha_inspector.engine import i18n

    rules_dir = Path(
        "custom_components/ha_inspector/engine/rules"
    )

    finding_ids: set[str] = set()

    for rule_file in sorted(rules_dir.glob("*.py")):
        tree = ast.parse(
            rule_file.read_text(encoding="utf-8")
        )

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.keyword)
                and node.arg == "finding_id"
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            ):
                finding_ids.add(node.value.value)

            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "finding_id"
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            ):
                finding_ids.add(node.value.value)

    # RepairIssuesRule generates these finding IDs from severity_config
    # instead of declaring them directly in Finding(finding_id=...).
    finding_ids.update(
        {
            "REPAIR_ISSUES_CRITICAL",
            "REPAIR_ISSUES_ERROR",
            "REPAIR_ISSUES_WARNING",
        }
    )

    spanish_translations = set(
        i18n._FINDING_TRANSLATIONS["es"]  # type: ignore[attr-defined]
    )

    assert spanish_translations == finding_ids



def test_localize_finding_returns_original_for_default_language() -> None:
    from custom_components.ha_inspector.engine.i18n import localize_finding
    from custom_components.ha_inspector.engine.models import Finding
    from custom_components.ha_inspector.engine.severity import Severity

    finding = Finding(
        finding_id="TEST_FINDING",
        severity=Severity.INFO,
        title="Original title",
        description="Original description",
        recommendation="Original recommendation",
        data={},
    )

    assert localize_finding(finding, "en") is finding


def test_localize_finding_returns_original_when_translation_missing() -> None:
    from custom_components.ha_inspector.engine.i18n import localize_finding
    from custom_components.ha_inspector.engine.models import Finding
    from custom_components.ha_inspector.engine.severity import Severity

    finding = Finding(
        finding_id="UNKNOWN_FINDING",
        severity=Severity.INFO,
        title="Original title",
        description="Original description",
        recommendation="Original recommendation",
        data={},
    )

    assert localize_finding(finding, "es") is finding


def test_localize_finding_falls_back_for_missing_or_invalid_fields(
    monkeypatch,
) -> None:
    from custom_components.ha_inspector.engine import i18n
    from custom_components.ha_inspector.engine.models import Finding
    from custom_components.ha_inspector.engine.severity import Severity

    monkeypatch.setitem(
        i18n._FINDING_TRANSLATIONS["es"],  # type: ignore[attr-defined]
        "TEST_FALLBACKS",
        {
            "title": "Invalid {missing_variable}",
        },
    )

    finding = Finding(
        finding_id="TEST_FALLBACKS",
        severity=Severity.INFO,
        title="Original title",
        description="Original description",
        recommendation="Original recommendation",
        data={},
    )

    localized = i18n.localize_finding(finding, "es")

    assert localized.title == finding.title
    assert localized.description == finding.description
    assert localized.recommendation == finding.recommendation

def test_localize_missing_entity_references_finding() -> None:
    from custom_components.ha_inspector.engine.i18n import localize_finding
    from custom_components.ha_inspector.engine.models import Finding
    from custom_components.ha_inspector.engine.severity import Severity

    finding = Finding(
        finding_id="MISSING_ENTITY_REFERENCES_FOUND",
        severity=Severity.ERROR,
        title="Missing entity references detected",
        description="2 referenced entities do not exist.",
        recommendation="Review affected configuration.",
        data={
            "missing_entity_count": 2,
            "missing_entities": [
                "light.removed_lamp",
                "sensor.old_temperature",
            ],
        },
    )

    localized = localize_finding(finding, "es")

    assert localized.title == (
        "Se han detectado referencias a entidades inexistentes"
    )
    assert localized.description == (
        "2 entidades referenciadas ya no existen."
    )
    assert localized.recommendation is not None
    assert "automatizaciones, scripts y escenas" in localized.recommendation
    assert localized.data == finding.data
