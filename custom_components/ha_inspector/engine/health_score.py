"""Health score calculation for HA Inspector."""

from __future__ import annotations

from collections.abc import Mapping

from .severity import Severity


SEVERITY_FACTOR: dict[Severity, float] = {
    Severity.INFO: 0.0,
    Severity.WARNING: 0.30,
    Severity.ERROR: 0.70,
    Severity.CRITICAL: 1.0,
}


class HealthScore:
    """Calculate global and category health scores."""

    MAX_SCORE = 100
    MIN_SCORE = 0

    @classmethod
    def calculate_penalty(
        cls,
        *,
        weight: int,
        severities: list[Severity],
    ) -> float:
        """Calculate the penalty produced by one inspection rule."""
        normalized_weight = max(0, weight)

        return sum(
            normalized_weight * SEVERITY_FACTOR[severity]
            for severity in severities
        )

    @classmethod
    def calculate(
        cls,
        penalties: Mapping[str, float],
    ) -> int:
        """Calculate the overall health score from category penalties."""
        total_penalty = sum(
            max(0.0, penalty)
            for penalty in penalties.values()
        )

        return cls._normalize(cls.MAX_SCORE - round(total_penalty))

    @classmethod
    def calculate_category(
        cls,
        penalty: float,
    ) -> int:
        """Calculate the health score for one category."""
        return cls._normalize(
            cls.MAX_SCORE - round(max(0.0, penalty))
        )

    @classmethod
    def _normalize(cls, score: int) -> int:
        """Keep a score inside the supported range."""
        return max(cls.MIN_SCORE, min(cls.MAX_SCORE, score))