"""Constants for the HA Inspector integration."""

from __future__ import annotations

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "ha_inspector"
NAME: Final = "HA Inspector"
VERSION: Final = "0.5.1"

PLATFORMS: Final = (Platform.SENSOR,)

DATA_LAST_RESULT: Final = "last_result"
DATA_RESTART_HISTORY: Final = "restart_history"
SIGNAL_INSPECTION_FINISHED: Final = f"{DOMAIN}_inspection_finished"
