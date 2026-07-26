"""Tests for the Home Assistant inspection service adapter."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from custom_components.ha_inspector.engine.inspection_service import (
    InspectionRequestError,
)
from custom_components.ha_inspector.service_adapter import (
    InspectionServiceAdapter,
    InspectionServiceAdapterError,
)


class FakeInspectionService:
    def __init__(self, result=None) -> None:
        self.result = result if result is not None else {"ok": True}
        self.calls = []

    async def run(self, context, request):
        self.calls.append((context, request))
        return self.result


class SerializableResult:
    def as_dict(self):
        return {
            "checks_executed": 2,
            "findings": [],
        }


class InvalidSerializableResult:
    def as_dict(self):
        return ["invalid"]


def make_adapter(result=None) -> InspectionServiceAdapter:
    return InspectionServiceAdapter(
        service=FakeInspectionService(result)
    )


def test_empty_data_builds_default_request() -> None:
    request = make_adapter().build_request()

    assert request.profile is None
    assert request.selection.include_rule_ids is None
    assert request.selection.include_categories is None
    assert request.selection.include_tags is None
    assert request.strict is True


def test_profile_data_builds_profile_request() -> None:
    request = make_adapter().build_request(
        {
            "profile": " quick ",
            "strict": False,
        }
    )

    assert request.profile == "quick"
    assert request.strict is False


def test_direct_selection_is_normalized() -> None:
    request = make_adapter().build_request(
        {
            "rule_ids": " system.core ",
            "categories": [" system "],
            "tags": (" core ", "version"),
            "exclude_tags": [" experimental "],
        }
    )

    assert request.selection.include_rule_ids == frozenset(
        {"system.core"}
    )
    assert request.selection.include_categories == frozenset(
        {"system"}
    )
    assert request.selection.include_tags == frozenset(
        {"core", "version"}
    )
    assert request.selection.exclude_tags == frozenset(
        {"experimental"}
    )


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(
        InspectionServiceAdapterError,
        match="unknown service fields: unsupported",
    ):
        make_adapter().build_request(
            {"unsupported": True}
        )


def test_strict_must_be_boolean() -> None:
    with pytest.raises(
        InspectionServiceAdapterError,
        match="strict must be a boolean",
    ):
        make_adapter().build_request(
            {"strict": "false"}
        )


def test_collections_reject_non_string_items() -> None:
    with pytest.raises(
        InspectionServiceAdapterError,
        match="tags must contain non-empty strings",
    ):
        make_adapter().build_request(
            {"tags": ["system", 123]}
        )


def test_profile_and_selection_conflict_is_preserved() -> None:
    with pytest.raises(
        InspectionRequestError,
        match=(
            "profile cannot be combined with direct selection criteria"
        ),
    ):
        make_adapter().build_request(
            {
                "profile": "quick",
                "categories": ["system"],
            }
        )


def test_built_request_is_immutable() -> None:
    request = make_adapter().build_request(
        {"categories": ["system"]}
    )

    with pytest.raises(FrozenInstanceError):
        request.strict = False  # type: ignore[misc]


@pytest.mark.asyncio
async def test_async_handle_delegates_to_service() -> None:
    service = FakeInspectionService(
        {"checks_executed": 1}
    )
    adapter = InspectionServiceAdapter(service=service)
    context = object()

    response = await adapter.async_handle(
        context,
        {"rule_ids": ["system.core"]},
    )

    assert response == {"checks_executed": 1}
    assert len(service.calls) == 1
    assert service.calls[0][0] is context
    assert (
        service.calls[0][1].selection.include_rule_ids
        == frozenset({"system.core"})
    )


@pytest.mark.asyncio
async def test_async_handle_serializes_as_dict_result() -> None:
    response = await make_adapter(
        SerializableResult()
    ).async_handle(object())

    assert response == {
        "checks_executed": 2,
        "findings": [],
    }


@pytest.mark.asyncio
async def test_async_handle_returns_isolated_mapping() -> None:
    original = {"checks_executed": 1}
    response = await make_adapter(
        original
    ).async_handle(object())

    response["checks_executed"] = 99

    assert original["checks_executed"] == 1


@pytest.mark.asyncio
async def test_invalid_result_is_rejected() -> None:
    with pytest.raises(
        InspectionServiceAdapterError,
        match="result.as_dict\\(\\) must return a mapping",
    ):
        await make_adapter(
            InvalidSerializableResult()
        ).async_handle(object())


@pytest.mark.asyncio
async def test_non_serializable_result_is_rejected() -> None:
    with pytest.raises(
        InspectionServiceAdapterError,
        match="inspection result is not serializable",
    ):
        await make_adapter(
            object()
        ).async_handle(object())
