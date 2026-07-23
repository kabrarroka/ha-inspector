"""Official inspection categories used by HA Inspector."""

from __future__ import annotations

from enum import StrEnum


class Category(StrEnum):
    """Official HA Inspector finding categories."""

    GENERAL = "general"

    SYSTEM = "system"
    RECORDER = "recorder"
    DATABASE = "database"

    INTEGRATIONS = "integrations"
    ENTITIES = "entities"

    AUTOMATIONS = "automations"
    SCRIPTS = "scripts"
    HELPERS = "helpers"
    TEMPLATES = "templates"

    MQTT = "mqtt"
    ZIGBEE = "zigbee"
    ESPHOME = "esphome"

    NETWORK = "network"
    STORAGE = "storage"
    PERFORMANCE = "performance"
    SECURITY = "security"

    BACKUPS = "backups"