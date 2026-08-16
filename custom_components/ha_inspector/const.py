"""Constants for the HA Inspector integration."""

from __future__ import annotations

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "ha_inspector"
NAME: Final = "HA Inspector"
VERSION: Final = "0.5.0"

PLATFORMS: Final = (Platform.SENSOR,)

DATA_LAST_RESULT: Final = "last_result"
SIGNAL_INSPECTION_FINISHED: Final = f"{DOMAIN}_inspection_finished"
