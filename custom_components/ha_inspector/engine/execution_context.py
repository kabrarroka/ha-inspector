"""Runtime execution state for the HA Inspector rule engine."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from time import perf_counter
from typing import TypeAlias

Clock: TypeAlias = Callable[[], float]


@dataclass(slots=True)
class ExecutionContext:
    """Track mutable state for one rule-engine execution.

    This context contains execution state only. Home Assistant inspection data
    remains in ``InspectionContext``.
    """

    total_rules: int
    clock: Clock = field(default=perf_counter, repr=False)
    started_at: float = field(init=False)
    finished_at: float | None = field(default=None, init=False)
    current_rule_id: str | None = field(default=None, init=False)
    current_rule_started_at: float | None = field(default=None, init=False)
    rules_executed: int = field(default=0, init=False)
    rules_succeeded: int = field(default=0, init=False)
    rules_failed: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        """Validate configuration and start the execution clock."""
        if self.total_rules < 0:
            raise ValueError("total_rules must be greater than or equal to zero")
        self.started_at = self.clock()

    @property
    def is_running(self) -> bool:
        """Return whether the execution has not been finished."""
        return self.finished_at is None

    @property
    def progress(self) -> float:
        """Return normalized progress between zero and one."""
        if self.total_rules == 0:
            return 1.0
        return min(1.0, self.rules_executed / self.total_rules)

    @property
    def duration_ms(self) -> float:
        """Return total elapsed execution time in milliseconds."""
        end = self.finished_at if self.finished_at is not None else self.clock()
        return max(0.0, (end - self.started_at) * 1000)

    def start_rule(self, rule_id: str) -> None:
        """Mark a rule as currently executing."""
        if not self.is_running:
            raise RuntimeError("execution is already finished")
        if self.current_rule_id is not None:
            raise RuntimeError(
                f"rule {self.current_rule_id!r} is already executing"
            )
        if self.rules_executed >= self.total_rules:
            raise RuntimeError("all configured rules have already executed")
        if not rule_id:
            raise ValueError("rule_id must not be empty")

        self.current_rule_id = rule_id
        self.current_rule_started_at = self.clock()

    def complete_rule(self, *, success: bool) -> float:
        """Complete the active rule and return its duration in milliseconds."""
        if self.current_rule_id is None or self.current_rule_started_at is None:
            raise RuntimeError("no rule is currently executing")

        finished_at = self.clock()
        duration_ms = max(
            0.0,
            (finished_at - self.current_rule_started_at) * 1000,
        )

        self.rules_executed += 1
        if success:
            self.rules_succeeded += 1
        else:
            self.rules_failed += 1

        self.current_rule_id = None
        self.current_rule_started_at = None
        return duration_ms

    def finish(self) -> None:
        """Mark the complete engine execution as finished."""
        if not self.is_running:
            return
        if self.current_rule_id is not None:
            raise RuntimeError("cannot finish while a rule is executing")
        if self.rules_executed != self.total_rules:
            raise RuntimeError(
                "cannot finish before all configured rules have executed"
            )

        self.finished_at = self.clock()
