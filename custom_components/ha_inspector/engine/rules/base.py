"""Base class for HA Inspector rules."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..context import InspectionContext
from ..models import Finding


class BaseRule(ABC):
    """Base class for inspection rules."""

    rule_id: str

    @abstractmethod
    async def check(
        self,
        context: InspectionContext,
    ) -> list[Finding]:
        """Evaluate the context and return inspection findings."""