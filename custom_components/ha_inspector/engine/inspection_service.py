"""Application service for executing HA Inspector inspections."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from .context import InspectionContext
from .execution_plan import RuleExecutionPlan
from .rule_profiles import RuleProfiles
from .rule_selector import RuleSelection, RuleSelectionError, RuleSelector


class InspectionRequestError(ValueError):
    """Raised when an inspection request is invalid."""


@dataclass(frozen=True, slots=True, init=False)
class InspectionRequest:
    """Normalized immutable request for an inspection execution."""

    profile: str | None
    selection: RuleSelection
    strict: bool

    def __init__(
        self,
        *,
        profile: str | None = None,
        rule_ids: Iterable[str] | None = None,
        categories: Iterable[str] | None = None,
        tags: Iterable[str] | None = None,
        exclude_rule_ids: Iterable[str] = (),
        exclude_categories: Iterable[str] = (),
        exclude_tags: Iterable[str] = (),
        strict: bool = True,
    ) -> None:
        normalized_profile = self._normalize_profile(profile)
        selection = RuleSelection(
            include_rule_ids=rule_ids,
            include_categories=categories,
            include_tags=tags,
            exclude_rule_ids=exclude_rule_ids,
            exclude_categories=exclude_categories,
            exclude_tags=exclude_tags,
        )

        if normalized_profile is not None and self._has_selection_criteria(
            selection
        ):
            raise InspectionRequestError(
                "profile cannot be combined with direct selection criteria"
            )

        object.__setattr__(self, "profile", normalized_profile)
        object.__setattr__(self, "selection", selection)
        object.__setattr__(self, "strict", bool(strict))

    @staticmethod
    def _normalize_profile(profile: str | None) -> str | None:
        if profile is None:
            return None
        if not isinstance(profile, str) or not profile.strip():
            raise InspectionRequestError(
                "profile must not be empty"
            )
        return profile.strip()

    @staticmethod
    def _has_selection_criteria(selection: RuleSelection) -> bool:
        return any(
            (
                selection.include_rule_ids is not None,
                selection.include_categories is not None,
                selection.include_tags is not None,
                bool(selection.exclude_rule_ids),
                bool(selection.exclude_categories),
                bool(selection.exclude_tags),
            )
        )

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-friendly request representation."""
        return {
            "profile": self.profile,
            "strict": self.strict,
            "selection": {
                "rule_ids": self._sorted_or_none(
                    self.selection.include_rule_ids
                ),
                "categories": self._sorted_or_none(
                    self.selection.include_categories
                ),
                "tags": self._sorted_or_none(
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


class InspectionService:
    """Resolve inspection requests and delegate execution to RuleEngine."""

    def __init__(
        self,
        *,
        engine: Any,
        selector: RuleSelector,
        profiles: RuleProfiles | None = None,
    ) -> None:
        self._engine = engine
        self._selector = selector
        self._profiles = profiles

    @property
    def selector(self) -> RuleSelector:
        """Return the configured rule selector."""
        return self._selector

    @property
    def profiles(self) -> RuleProfiles | None:
        """Return the optional profile registry."""
        return self._profiles

    def build_plan(
        self,
        request: InspectionRequest,
    ) -> RuleExecutionPlan:
        """Translate an inspection request into an execution plan."""
        if request.profile is not None:
            if self._profiles is None:
                raise InspectionRequestError(
                    "inspection profiles are not configured"
                )
            return self._profiles.select(
                request.profile,
                self._selector,
                strict=request.strict,
            )

        selection = request.selection
        return self._selector.select(
            include_rule_ids=selection.include_rule_ids,
            include_categories=selection.include_categories,
            include_tags=selection.include_tags,
            exclude_rule_ids=selection.exclude_rule_ids,
            exclude_categories=selection.exclude_categories,
            exclude_tags=selection.exclude_tags,
            strict=request.strict,
        )

    async def run(
        self,
        context: InspectionContext,
        request: InspectionRequest | None = None,
    ) -> Any:
        """Build and execute one inspection plan."""
        effective_request = request or InspectionRequest()
        plan = self.build_plan(effective_request)
        return await self._engine.run_plan(context, plan)


__all__ = [
    "InspectionRequest",
    "InspectionRequestError",
    "InspectionService",
    "RuleSelectionError",
]
