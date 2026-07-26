"""Constants for the HA Inspector integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "ha_inspector"
NAME: Final = "HA Inspector"

PLATFORMS: Final = ["sensor"]

DATA_LAST_RESULT: Final = "last_result"
SIGNAL_INSPECTION_FINISHED: Final = f"{DOMAIN}_inspection_finished"
