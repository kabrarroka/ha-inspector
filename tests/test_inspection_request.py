from __future__ import annotations

from custom_components.ha_inspector.engine.request import InspectionRequest


def test_default_request():
    request = InspectionRequest()

    assert request.include_rule_ids == ()
    assert request.exclude_rule_ids == ()
    assert request.diagnostics is False


def test_request_normalizes_filters():
    request = InspectionRequest(
        include_rule_ids=(" RULE2 ", "RULE1", "RULE1", ""),
        include_categories=("system", " entities "),
        include_tags=("core", "core"),
    )

    assert request.include_rule_ids == ("RULE1", "RULE2")
    assert request.include_categories == ("entities", "system")
    assert request.include_tags == ("core",)


def test_request_accepts_single_strings():
    request = InspectionRequest(
        include_rule_ids="RULE1",
        exclude_categories="storage",
    )

    assert request.include_rule_ids == ("RULE1",)
    assert request.exclude_categories == ("storage",)


def test_request_from_empty_dict():
    assert InspectionRequest.from_dict({}) == InspectionRequest()
    assert InspectionRequest.from_dict(None) == InspectionRequest()


def test_request_from_dict():
    request = InspectionRequest.from_dict(
        {
            "include_categories": ["system", "entities"],
            "exclude_tags": ["experimental"],
            "diagnostics": True,
        }
    )

    assert request.include_categories == ("entities", "system")
    assert request.exclude_tags == ("experimental",)
    assert request.diagnostics is True


def test_selector_options():
    request = InspectionRequest(
        include_rule_ids=("RULE1",),
        exclude_tags=("experimental",),
        diagnostics=True,
    )

    assert request.selector_options() == {
        "include_rule_ids": ("RULE1",),
        "include_categories": (),
        "include_tags": (),
        "exclude_rule_ids": (),
        "exclude_categories": (),
        "exclude_tags": ("experimental",),
    }


def test_as_dict_is_json_safe():
    request = InspectionRequest(
        include_rule_ids=("RULE1",),
        diagnostics=True,
    )

    assert request.as_dict() == {
        "include_rule_ids": ["RULE1"],
        "include_categories": [],
        "include_tags": [],
        "exclude_rule_ids": [],
        "exclude_categories": [],
        "exclude_tags": [],
        "diagnostics": True,
        "language": None,
    }


def test_language_is_normalized_as_request_value() -> None:
    request = InspectionRequest.from_dict(
        {
            "language": " es-ES ",
        }
    )

    assert request.language == "es-ES"
    assert request.as_dict()["language"] == "es-ES"
