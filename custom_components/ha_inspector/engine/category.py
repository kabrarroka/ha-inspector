"""Categories used to classify HA Inspector rules."""

from __future__ import annotations

from enum import StrEnum


class Category(StrEnum):
    """Rule categories."""

    SYSTEM = "system"
    STORAGE = "storage"
    RECORDER = "recorder"
    DATABASE = "database"
    NETWORK = "network"
    HARDWARE = "hardware"
    INTEGRATIONS = "integrations"
    ENTITIES = "entities"
    AUTOMATIONS = "automations"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DIAGNOSTICS = "diagnostics"
    