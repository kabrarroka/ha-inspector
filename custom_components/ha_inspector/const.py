"""Constants for the HA Inspector integration."""

from __future__ import annotations

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "ha_inspector"
NAME: Final = "HA Inspector"
VERSION: Final = "1.3.1"

PLATFORMS: Final = (Platform.SENSOR,)

DATA_LAST_RESULT: Final = "last_result"
DATA_INSPECTION_HISTORY: Final = "inspection_history"
DATA_ACKNOWLEDGEMENTS: Final = "acknowledgements"
DATA_RESTART_HISTORY: Final = "restart_history"
SIGNAL_INSPECTION_FINISHED: Final = f"{DOMAIN}_inspection_finished"
