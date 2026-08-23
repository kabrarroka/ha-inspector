"""Historical inspection comparison for HA Inspector."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class HistoricalInspectionComparison:
    """Compare two compact historical inspection entries."""

    previous_score: int | None
    current_score: int | None
    score_delta: int | None
    previous_status: str | None
    current_status: str | None
    previous_findings: int | None
    current_findings: int | None
    findings_delta: int | None

    def as_dict(self) -> dict[str, int | str | None]:
        """Return a JSON-serializable representation."""
        return {
            "previous_score": self.previous_score,
            "current_score": self.current_score,
            "score_delta": self.score_delta,
            "previous_status": self.previous_status,
            "current_status": self.current_status,
            "previous_findings": self.previous_findings,
            "current_findings": self.current_findings,
            "findings_delta": self.findings_delta,
        }


def compare_history_entries(
    previous: dict[str, Any],
    current: dict[str, Any],
) -> HistoricalInspectionComparison:
    """Compare two compact historical inspection entries."""
    previous_score = _valid_int(previous.get("score"))
    current_score = _valid_int(current.get("score"))
    previous_findings = _valid_int(previous.get("total_findings"))
    current_findings = _valid_int(current.get("total_findings"))

    return HistoricalInspectionComparison(
        previous_score=previous_score,
        current_score=current_score,
        score_delta=_delta(previous_score, current_score),
        previous_status=_valid_str(previous.get("status")),
        current_status=_valid_str(current.get("status")),
        previous_findings=previous_findings,
        current_findings=current_findings,
        findings_delta=_delta(previous_findings, current_findings),
    )


def _valid_int(value: Any) -> int | None:
    """Return an integer value, excluding booleans."""
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def _valid_str(value: Any) -> str | None:
    """Return a string value."""
    return value if isinstance(value, str) else None


def _delta(
    previous: int | None,
    current: int | None,
) -> int | None:
    """Return a delta when both values are available."""
    if previous is None or current is None:
        return None
    return current - previous


@dataclass(frozen=True, slots=True)
class HistoricalDomainComparison:
    """Compare one domain between historical inspection entries."""

    domain: str
    previous_score: int | None
    current_score: int | None
    score_delta: int | None
    previous_status: str | None
    current_status: str | None

    def as_dict(self) -> dict[str, int | str | None]:
        """Return a JSON-serializable representation."""
        return {
            "domain": self.domain,
            "previous_score": self.previous_score,
            "current_score": self.current_score,
            "score_delta": self.score_delta,
            "previous_status": self.previous_status,
            "current_status": self.current_status,
        }


def compare_history_domains(
    previous: dict[str, Any],
    current: dict[str, Any],
) -> dict[str, HistoricalDomainComparison]:
    """Compare domain health between two historical entries."""
    previous_domains = _domain_health(previous)
    current_domains = _domain_health(current)

    domains = sorted(
        set(previous_domains) | set(current_domains)
    )

    return {
        domain: _compare_domain(
            domain,
            previous_domains.get(domain),
            current_domains.get(domain),
        )
        for domain in domains
    }


def _domain_health(
    entry: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Return valid domain-health mappings."""
    domain_health = entry.get("domain_health")

    if not isinstance(domain_health, dict):
        return {}

    return {
        domain: data
        for domain, data in domain_health.items()
        if isinstance(domain, str) and isinstance(data, dict)
    }


def _compare_domain(
    domain: str,
    previous: dict[str, Any] | None,
    current: dict[str, Any] | None,
) -> HistoricalDomainComparison:
    """Compare one historical domain."""
    previous_score, previous_status = _domain_values(previous)
    current_score, current_status = _domain_values(current)

    return HistoricalDomainComparison(
        domain=domain,
        previous_score=previous_score,
        current_score=current_score,
        score_delta=_delta(previous_score, current_score),
        previous_status=previous_status,
        current_status=current_status,
    )


def _domain_values(
    data: dict[str, Any] | None,
) -> tuple[int | None, str | None]:
    """Extract score and status from a domain-health entry."""
    if data is None:
        return None, None

    health = data.get("health")
    if not isinstance(health, dict):
        return None, _valid_str(data.get("status"))

    return (
        _valid_int(health.get("score")),
        _valid_str(health.get("status")),
    )
