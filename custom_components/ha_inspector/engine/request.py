"""Public inspection request model."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any


def _normalize(values: Iterable[str] | None) -> tuple[str, ...]:
    """Normalize string filters into a deterministic tuple."""
    if values is None:
        return ()

    if isinstance(values, str):
        values = (values,)

    return tuple(
        sorted(
            {
                value.strip()
                for value in values
                if isinstance(value, str) and value.strip()
            }
        )
    )


@dataclass(frozen=True, slots=True)
class InspectionRequest:
    """Describe one inspection execution request."""

    include_rule_ids: tuple[str, ...] = field(default_factory=tuple)
    include_categories: tuple[str, ...] = field(default_factory=tuple)
    include_tags: tuple[str, ...] = field(default_factory=tuple)

    exclude_rule_ids: tuple[str, ...] = field(default_factory=tuple)
    exclude_categories: tuple[str, ...] = field(default_factory=tuple)
    exclude_tags: tuple[str, ...] = field(default_factory=tuple)

    diagnostics: bool = False

    def __post_init__(self) -> None:
        """Normalize all request filters."""
        object.__setattr__(
            self,
            "include_rule_ids",
            _normalize(self.include_rule_ids),
        )
        object.__setattr__(
            self,
            "include_categories",
            _normalize(self.include_categories),
        )
        object.__setattr__(
            self,
            "include_tags",
            _normalize(self.include_tags),
        )
        object.__setattr__(
            self,
            "exclude_rule_ids",
            _normalize(self.exclude_rule_ids),
        )
        object.__setattr__(
            self,
            "exclude_categories",
            _normalize(self.exclude_categories),
        )
        object.__setattr__(
            self,
            "exclude_tags",
            _normalize(self.exclude_tags),
        )

        object.__setattr__(
            self,
            "diagnostics",
            bool(self.diagnostics),
        )

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any] | None,
    ) -> InspectionRequest:
        """Create a request from untrusted mapping data."""
        if not data:
            return cls()

        return cls(
            include_rule_ids=_normalize(data.get("include_rule_ids")),
            include_categories=_normalize(data.get("include_categories")),
            include_tags=_normalize(data.get("include_tags")),
            exclude_rule_ids=_normalize(data.get("exclude_rule_ids")),
            exclude_categories=_normalize(data.get("exclude_categories")),
            exclude_tags=_normalize(data.get("exclude_tags")),
            diagnostics=bool(data.get("diagnostics", False)),
        )

    def selector_options(self) -> dict[str, tuple[str, ...]]:
        """Return keyword arguments accepted by RuleSelector.select."""
        return {
            "include_rule_ids": self.include_rule_ids,
            "include_categories": self.include_categories,
            "include_tags": self.include_tags,
            "exclude_rule_ids": self.exclude_rule_ids,
            "exclude_categories": self.exclude_categories,
            "exclude_tags": self.exclude_tags,
        }

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "include_rule_ids": list(self.include_rule_ids),
            "include_categories": list(self.include_categories),
            "include_tags": list(self.include_tags),
            "exclude_rule_ids": list(self.exclude_rule_ids),
            "exclude_categories": list(self.exclude_categories),
            "exclude_tags": list(self.exclude_tags),
            "diagnostics": self.diagnostics,
        }


__all__ = ["InspectionRequest"]
