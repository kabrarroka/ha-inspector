"""Base class for HA Inspector collectors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ..context import InspectionContext

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class BaseCollector(ABC):
    """Base class for inspection data collectors."""

    collector_id: str

    @abstractmethod
    async def collect(
        self,
        hass: HomeAssistant,
        context: InspectionContext,
    ) -> None:
        """Collect data and store it in the inspection context."""