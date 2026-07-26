"""Tests for the rule-engine execution context."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from custom_components.ha_inspector.engine.execution_context import (
    ExecutionContext,
)


class SequenceClock:
    """Return deterministic monotonic values."""

    def __init__(self, *values: float) -> None:
        self._values: Iterator[float] = iter(values)

    def __call__(self) -> float:
        return next(self._values)


def test_execution_context_tracks_success_and_progress() -> None:
    context = ExecutionContext(
        total_rules=2,
        clock=SequenceClock(1.0, 1.1, 1.125),
    )

    context.start_rule("test.success")
    duration_ms = context.complete_rule(success=True)

    assert duration_ms == pytest.approx(25.0)
    assert context.rules_executed == 1
    assert context.rules_succeeded == 1
    assert context.rules_failed == 0
    assert context.progress == pytest.approx(0.5)
    assert context.current_rule_id is None


def test_execution_context_tracks_failed_rule() -> None:
    context = ExecutionContext(
        total_rules=1,
        clock=SequenceClock(2.0, 2.1, 2.15),
    )

    context.start_rule("test.failure")
    duration_ms = context.complete_rule(success=False)

    assert duration_ms == pytest.approx(50.0)
    assert context.rules_executed == 1
    assert context.rules_succeeded == 0
    assert context.rules_failed == 1
    assert context.progress == 1.0


def test_finish_records_stable_total_duration() -> None:
    context = ExecutionContext(
        total_rules=1,
        clock=SequenceClock(10.0, 10.01, 10.02, 10.05),
    )

    context.start_rule("test.rule")
    context.complete_rule(success=True)
    context.finish()

    assert context.is_running is False
    assert context.duration_ms == pytest.approx(50.0)
    assert context.duration_ms == pytest.approx(50.0)


def test_empty_execution_can_finish_immediately() -> None:
    context = ExecutionContext(
        total_rules=0,
        clock=SequenceClock(3.0, 3.01),
    )

    assert context.progress == 1.0

    context.finish()

    assert context.is_running is False
    assert context.rules_executed == 0
    assert context.duration_ms == pytest.approx(10.0)


def test_invalid_state_transitions_are_rejected() -> None:
    context = ExecutionContext(
        total_rules=2,
        clock=SequenceClock(1.0, 1.1),
    )

    with pytest.raises(RuntimeError, match="no rule"):
        context.complete_rule(success=True)

    context.start_rule("test.first")

    with pytest.raises(RuntimeError, match="already executing"):
        context.start_rule("test.second")

    with pytest.raises(RuntimeError, match="while a rule"):
        context.finish()


def test_total_rules_cannot_be_negative() -> None:
    with pytest.raises(ValueError, match="total_rules"):
        ExecutionContext(total_rules=-1)


def test_finish_requires_all_rules_to_have_executed() -> None:
    context = ExecutionContext(
        total_rules=1,
        clock=SequenceClock(1.0),
    )

    with pytest.raises(RuntimeError, match="before all configured rules"):
        context.finish()
