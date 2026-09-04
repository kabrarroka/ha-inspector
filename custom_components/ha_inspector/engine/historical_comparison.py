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


@dataclass(frozen=True, slots=True)
class HistoricalRemediationComparison:
    """Compare remediation lifecycle between historical inspections."""

    previous_tracked_entities: int | None
    current_tracked_entities: int | None
    tracked_entities_delta: int | None
    previous_pending: int | None
    current_pending: int | None
    pending_delta: int | None
    previous_in_progress: int | None
    current_in_progress: int | None
    in_progress_delta: int | None
    previous_resolved: int | None
    current_resolved: int | None
    resolved_delta: int | None
    previous_completed_actions: int | None
    current_completed_actions: int | None
    completed_actions_delta: int | None
    previous_remaining_actions: int | None
    current_remaining_actions: int | None
    remaining_actions_delta: int | None
    previous_new_references: int | None
    current_new_references: int | None
    new_references_delta: int | None

    def as_dict(self) -> dict[str, int | None]:
        """Return a JSON-serializable representation."""
        return {
            "previous_tracked_entities": self.previous_tracked_entities,
            "current_tracked_entities": self.current_tracked_entities,
            "tracked_entities_delta": self.tracked_entities_delta,
            "previous_pending": self.previous_pending,
            "current_pending": self.current_pending,
            "pending_delta": self.pending_delta,
            "previous_in_progress": self.previous_in_progress,
            "current_in_progress": self.current_in_progress,
            "in_progress_delta": self.in_progress_delta,
            "previous_resolved": self.previous_resolved,
            "current_resolved": self.current_resolved,
            "resolved_delta": self.resolved_delta,
            "previous_completed_actions": self.previous_completed_actions,
            "current_completed_actions": self.current_completed_actions,
            "completed_actions_delta": self.completed_actions_delta,
            "previous_remaining_actions": self.previous_remaining_actions,
            "current_remaining_actions": self.current_remaining_actions,
            "remaining_actions_delta": self.remaining_actions_delta,
            "previous_new_references": self.previous_new_references,
            "current_new_references": self.current_new_references,
            "new_references_delta": self.new_references_delta,
        }


def compare_remediation_history(
    previous: dict[str, Any],
    current: dict[str, Any],
) -> HistoricalRemediationComparison:
    """Compare remediation lifecycle between historical entries."""
    previous_remediation = _remediation_history(previous)
    current_remediation = _remediation_history(current)

    previous_tracked = _valid_int(
        previous_remediation.get("tracked_entities")
    )
    current_tracked = _valid_int(
        current_remediation.get("tracked_entities")
    )
    previous_pending = _valid_int(
        previous_remediation.get("pending")
    )
    current_pending = _valid_int(
        current_remediation.get("pending")
    )
    previous_in_progress = _valid_int(
        previous_remediation.get("in_progress")
    )
    current_in_progress = _valid_int(
        current_remediation.get("in_progress")
    )
    previous_resolved = _valid_int(
        previous_remediation.get("resolved")
    )
    current_resolved = _valid_int(
        current_remediation.get("resolved")
    )
    previous_completed = _valid_int(
        previous_remediation.get("completed_actions")
    )
    current_completed = _valid_int(
        current_remediation.get("completed_actions")
    )
    previous_remaining = _valid_int(
        previous_remediation.get("remaining_actions")
    )
    current_remaining = _valid_int(
        current_remediation.get("remaining_actions")
    )
    previous_new_references = _valid_int(
        previous_remediation.get("new_references")
    )
    current_new_references = _valid_int(
        current_remediation.get("new_references")
    )

    return HistoricalRemediationComparison(
        previous_tracked_entities=previous_tracked,
        current_tracked_entities=current_tracked,
        tracked_entities_delta=_delta(
            previous_tracked,
            current_tracked,
        ),
        previous_pending=previous_pending,
        current_pending=current_pending,
        pending_delta=_delta(
            previous_pending,
            current_pending,
        ),
        previous_in_progress=previous_in_progress,
        current_in_progress=current_in_progress,
        in_progress_delta=_delta(
            previous_in_progress,
            current_in_progress,
        ),
        previous_resolved=previous_resolved,
        current_resolved=current_resolved,
        resolved_delta=_delta(
            previous_resolved,
            current_resolved,
        ),
        previous_completed_actions=previous_completed,
        current_completed_actions=current_completed,
        completed_actions_delta=_delta(
            previous_completed,
            current_completed,
        ),
        previous_remaining_actions=previous_remaining,
        current_remaining_actions=current_remaining,
        remaining_actions_delta=_delta(
            previous_remaining,
            current_remaining,
        ),
        previous_new_references=previous_new_references,
        current_new_references=current_new_references,
        new_references_delta=_delta(
            previous_new_references,
            current_new_references,
        ),
    )


def _remediation_history(
    entry: dict[str, Any],
) -> dict[str, Any]:
    """Return valid remediation history data."""
    remediation = entry.get("remediation")
    return remediation if isinstance(remediation, dict) else {}
