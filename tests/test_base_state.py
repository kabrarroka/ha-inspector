"""Tests for the common typed-state behaviour."""

from dataclasses import dataclass, field

from custom_components.ha_inspector.engine.base_state import BaseState


@dataclass(slots=True)
class ExampleState(BaseState):
    """Small state used to test shared serialization."""

    name: str = "example"
    items: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)


def test_base_state_as_dict_serializes_dataclass() -> None:
    state = ExampleState(
        name="test",
        items=["one"],
        metadata={"source": "test"},
    )

    assert state.as_dict() == {
        "name": "test",
        "items": ["one"],
        "metadata": {"source": "test"},
    }


def test_base_state_as_dict_returns_independent_mutable_values() -> None:
    state = ExampleState(
        items=["one"],
        metadata={"source": "original"},
    )

    first = state.as_dict()
    second = state.as_dict()

    first["items"].append("mutated")
    first["metadata"]["source"] = "mutated"

    assert second["items"] == ["one"]
    assert second["metadata"] == {"source": "original"}

    assert state.items == ["one"]
    assert state.metadata == {"source": "original"}