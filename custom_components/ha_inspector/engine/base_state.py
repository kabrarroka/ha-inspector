"""Base state model for HA Inspector."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class BaseState:
    """Provide common behaviour for typed inspection states."""

    def as_dict(self) -> dict[str, Any]:
        """Return a deep-copied dictionary representation of the state."""
        return asdict(self)