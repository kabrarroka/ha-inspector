"""Home Assistant-facing adapter for the inspection application service."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .engine.inspection_service import (
    InspectionRequest,
    InspectionRequestError,
    InspectionService,
)


class InspectionServiceAdapterError(ValueError):
    """Raised when service data cannot be converted into a request."""


@dataclass(frozen=True, slots=True)
class InspectionServiceAdapter:
    """Translate service data into inspection application calls."""

    service: InspectionService

    def build_request(
        self,
        data: Mapping[str, Any] | None = None,
    ) -> InspectionRequest:
        """Build an immutable inspection request from service data."""
        payload = dict(data or {})
        allowed = {
            "profile",
            "rule_ids",
            "categories",
            "tags",
            "exclude_rule_ids",
            "exclude_categories",
            "exclude_tags",
            "strict",
        }
        unknown = sorted(set(payload) - allowed)
        if unknown:
            raise InspectionServiceAdapterError(
                "unknown service fields: " + ", ".join(unknown)
            )

        try:
            return InspectionRequest(
                profile=payload.get("profile"),
                rule_ids=self._optional_collection(
                    payload,
                    "rule_ids",
                ),
                categories=self._optional_collection(
                    payload,
                    "categories",
                ),
                tags=self._optional_collection(
                    payload,
                    "tags",
                ),
                exclude_rule_ids=self._collection(
                    payload,
                    "exclude_rule_ids",
                ),
                exclude_categories=self._collection(
                    payload,
                    "exclude_categories",
                ),
                exclude_tags=self._collection(
                    payload,
                    "exclude_tags",
                ),
                strict=self._strict(payload),
            )
        except InspectionRequestError:
            raise
        except (TypeError, ValueError) as err:
            raise InspectionServiceAdapterError(str(err)) from err

    async def async_handle(
        self,
        context: Any,
        data: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute an inspection and return service-response data."""
        request = self.build_request(data)
        result = await self.service.run(context, request)
        return self._serialize_result(result)

    @staticmethod
    def _optional_collection(
        payload: Mapping[str, Any],
        key: str,
    ) -> tuple[str, ...] | None:
        if key not in payload or payload[key] is None:
            return None
        return InspectionServiceAdapter._normalize_collection(
            payload[key],
            key,
        )

    @staticmethod
    def _collection(
        payload: Mapping[str, Any],
        key: str,
    ) -> tuple[str, ...]:
        if key not in payload or payload[key] is None:
            return ()
        return InspectionServiceAdapter._normalize_collection(
            payload[key],
            key,
        )

    @staticmethod
    def _normalize_collection(
        value: Any,
        field: str,
    ) -> tuple[str, ...]:
        if isinstance(value, str):
            values = (value,)
        else:
            try:
                values = tuple(value)
            except TypeError as err:
                raise InspectionServiceAdapterError(
                    f"{field} must be a string or collection of strings"
                ) from err

        normalized: list[str] = []
        for item in values:
            if not isinstance(item, str) or not item.strip():
                raise InspectionServiceAdapterError(
                    f"{field} must contain non-empty strings"
                )
            normalized.append(item.strip())

        return tuple(normalized)

    @staticmethod
    def _strict(payload: Mapping[str, Any]) -> bool:
        value = payload.get("strict", True)
        if not isinstance(value, bool):
            raise InspectionServiceAdapterError(
                "strict must be a boolean"
            )
        return value

    @staticmethod
    def _serialize_result(result: Any) -> dict[str, Any]:
        if isinstance(result, Mapping):
            return dict(result)

        as_dict = getattr(result, "as_dict", None)
        if callable(as_dict):
            serialized = as_dict()
            if not isinstance(serialized, Mapping):
                raise InspectionServiceAdapterError(
                    "result.as_dict() must return a mapping"
                )
            return dict(serialized)

        raise InspectionServiceAdapterError(
            "inspection result is not serializable"
        )


__all__ = [
    "InspectionServiceAdapter",
    "InspectionServiceAdapterError",
]
