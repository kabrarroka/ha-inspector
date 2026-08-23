"""Historical trend analysis for HA Inspector."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

TrendDirection = Literal[
    "improving",
    "stable",
    "declining",
    "insufficient_data",
]


@dataclass(frozen=True, slots=True)
class ScoreTrend:
    """Describe the health-score trend across inspection history."""

    direction: TrendDirection
    samples: int
    first_score: int | None
    last_score: int | None
    delta: int | None

    def as_dict(self) -> dict[str, int | str | None]:
        """Return a JSON-serializable representation."""
        return {
            "direction": self.direction,
            "samples": self.samples,
            "first_score": self.first_score,
            "last_score": self.last_score,
            "delta": self.delta,
        }


def health_score_trend(
    entries: list[dict[str, Any]],
) -> ScoreTrend:
    """Return the health-score trend for valid history entries."""
    scores = [
        score
        for entry in entries
        if isinstance((score := entry.get("score")), int)
        and not isinstance(score, bool)
    ]

    if len(scores) < 2:
        only_score = scores[0] if scores else None
        return ScoreTrend(
            direction="insufficient_data",
            samples=len(scores),
            first_score=only_score,
            last_score=only_score,
            delta=None,
        )

    first_score = scores[0]
    last_score = scores[-1]
    delta = last_score - first_score

    if delta > 0:
        direction: TrendDirection = "improving"
    elif delta < 0:
        direction = "declining"
    else:
        direction = "stable"

    return ScoreTrend(
        direction=direction,
        samples=len(scores),
        first_score=first_score,
        last_score=last_score,
        delta=delta,
    )
