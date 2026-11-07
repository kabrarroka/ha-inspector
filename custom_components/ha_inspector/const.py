"""Constants for the HA Inspector integration."""

from __future__ import annotations

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "ha_inspector"
NAME: Final = "HA Inspector"
VERSION: Final = "1.7.0"

PLATFORMS: Final = (Platform.SENSOR,)

DATA_LAST_RESULT: Final = "last_result"
DATA_INSPECTION_HISTORY: Final = "inspection_history"
DATA_ACKNOWLEDGEMENTS: Final = "acknowledgements"
DATA_REMEDIATION_BASELINES: Final = "remediation_baselines"
DATA_REMEDIATION_STATE: Final = "remediation_state"
DATA_RESTART_HISTORY: Final = "restart_history"
DATA_PERIODIC_SCHEDULER: Final = "periodic_scheduler"
DATA_PERIODIC_RUNNER: Final = "async_run_periodic_inspection"
SIGNAL_INSPECTION_FINISHED: Final = f"{DOMAIN}_inspection_finished"

# Periodic inspection configuration.
CONF_PERIODIC_INSPECTION_ENABLED: Final = "periodic_inspection_enabled"
CONF_PERIODIC_INSPECTION_INTERVAL: Final = "periodic_inspection_interval"
CONF_PERIODIC_INSPECTION_PROFILE: Final = "periodic_inspection_profile"

DEFAULT_PERIODIC_INSPECTION_ENABLED: Final = False
DEFAULT_PERIODIC_INSPECTION_INTERVAL: Final = 60
DEFAULT_PERIODIC_INSPECTION_PROFILE: Final = "quick"

MIN_PERIODIC_INSPECTION_INTERVAL: Final = 5
MAX_PERIODIC_INSPECTION_INTERVAL: Final = 1440
