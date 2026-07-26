"""Immutable rule profile definitions for HA Inspector."""

from __future__ import annotations

from dataclasses import dataclass

from .rule_selector import RuleSelection


class RuleProfileError(ValueError):
    """Raised when a rule profile definition is invalid."""


@dataclass(frozen=True, slots=True)
class RuleProfile:
    """Named reusable rule selection."""

    name: str
    selection: RuleSelection
    title: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        normalized_name = self.name.strip()
        if not normalized_name:
            raise RuleProfileError("Profile name must not be empty")

        object.__setattr__(self, "name", normalized_name)

        if self.title is not None:
            normalized_title = self.title.strip()
            if not normalized_title:
                raise RuleProfileError(
                    f"Profile {normalized_name!r} has an empty title"
                )
            object.__setattr__(self, "title", normalized_title)

        if self.description is not None:
            normalized_description = self.description.strip()
            if not normalized_description:
                raise RuleProfileError(
                    f"Profile {normalized_name!r} has an empty description"
                )
            object.__setattr__(
                self,
                "description",
                normalized_description,
            )

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-friendly profile representation."""
        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "selection": {
                "include_rule_ids": self._sorted_or_none(
                    self.selection.include_rule_ids
                ),
                "include_categories": self._sorted_or_none(
                    self.selection.include_categories
                ),
                "include_tags": self._sorted_or_none(
                    self.selection.include_tags
                ),
                "exclude_rule_ids": sorted(
                    self.selection.exclude_rule_ids
                ),
                "exclude_categories": sorted(
                    self.selection.exclude_categories
                ),
                "exclude_tags": sorted(
                    self.selection.exclude_tags
                ),
            },
        }

    @staticmethod
    def _sorted_or_none(
        values: frozenset[str] | None,
    ) -> list[str] | None:
        if values is None:
            return None
        return sorted(values)


__all__ = [
    "RuleProfile",
    "RuleProfileError",
]
