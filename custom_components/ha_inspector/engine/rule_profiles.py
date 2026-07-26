"""Registry and execution helpers for HA Inspector rule profiles."""

from __future__ import annotations

from collections.abc import Iterator, Sequence

from .execution_plan import RuleExecutionPlan
from .rule_profile import RuleProfile, RuleProfileError
from .rule_selector import RuleSelector


class RuleProfiles:
    """Immutable registry of named rule profiles."""

    def __init__(self, profiles: Sequence[RuleProfile]) -> None:
        entries: dict[str, RuleProfile] = {}

        for profile in profiles:
            if profile.name in entries:
                raise RuleProfileError(
                    f"Duplicate profile name {profile.name!r}"
                )
            entries[profile.name] = profile

        self._profiles = entries
        self._ordered_profiles = tuple(
            entries[name]
            for name in sorted(entries)
        )

    def __len__(self) -> int:
        """Return the number of registered profiles."""
        return len(self._ordered_profiles)

    def __iter__(self) -> Iterator[RuleProfile]:
        """Iterate through profiles in deterministic name order."""
        return iter(self._ordered_profiles)

    def __contains__(self, name: object) -> bool:
        """Return whether a profile is registered."""
        return name in self._profiles

    @property
    def names(self) -> tuple[str, ...]:
        """Return registered profile names."""
        return tuple(profile.name for profile in self._ordered_profiles)

    def list_profiles(self) -> tuple[RuleProfile, ...]:
        """Return all profiles in deterministic order."""
        return self._ordered_profiles

    def get(self, name: str) -> RuleProfile:
        """Return one profile or raise KeyError."""
        try:
            return self._profiles[name]
        except KeyError:
            raise KeyError(f"Unknown rule profile: {name}") from None

    def select(
        self,
        name: str,
        selector: RuleSelector,
        *,
        strict: bool = True,
    ) -> RuleExecutionPlan:
        """Translate a named profile into an execution plan."""
        profile = self.get(name)
        selection = profile.selection

        return selector.select(
            include_rule_ids=selection.include_rule_ids,
            include_categories=selection.include_categories,
            include_tags=selection.include_tags,
            exclude_rule_ids=selection.exclude_rule_ids,
            exclude_categories=selection.exclude_categories,
            exclude_tags=selection.exclude_tags,
            strict=strict,
        )

    def as_dicts(self) -> list[dict[str, object]]:
        """Return JSON-friendly copies of all profiles."""
        return [
            profile.as_dict()
            for profile in self._ordered_profiles
        ]


__all__ = ["RuleProfiles"]
