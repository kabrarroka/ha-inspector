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


@dataclass(frozen=True, slots=True)
class DomainTrend:
    """Describe the historical health-score trend for one domain."""

    domain: str
    trend: ScoreTrend

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "domain": self.domain,
            **self.trend.as_dict(),
        }


def domain_health_trends(
    entries: list[dict[str, Any]],
) -> dict[str, DomainTrend]:
    """Return health-score trends for domains present in history."""
    domains: set[str] = set()
    domain_entries: dict[str, list[dict[str, Any]]] = {}

    for entry in entries:
        domain_health = entry.get("domain_health")

        if not isinstance(domain_health, dict):
            continue

        for domain, domain_data in domain_health.items():
            if not isinstance(domain, str) or not isinstance(
                domain_data,
                dict,
            ):
                continue

            domains.add(domain)

            health = domain_data.get("health")
            if not isinstance(health, dict):
                continue

            score = health.get("score")
            if not isinstance(score, int) or isinstance(score, bool):
                continue

            domain_entries.setdefault(domain, []).append(
                {
                    "score": score,
                }
            )

    return {
        domain: DomainTrend(
            domain=domain,
            trend=health_score_trend(
                domain_entries.get(domain, [])
            ),
        )
        for domain in sorted(domains)
    }
