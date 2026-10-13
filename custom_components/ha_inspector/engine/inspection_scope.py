"""Stable identity for comparable inspection requests."""

from __future__ import annotations

import json

from .request import InspectionRequest


def inspection_scope(request: InspectionRequest) -> str:
    """Return a deterministic identity for inspection rule filters."""
    filters = request.selector_options()

    return json.dumps(
        filters,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


__all__ = ["inspection_scope"]
