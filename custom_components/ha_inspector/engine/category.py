"""Categories used to classify HA Inspector rules."""

from __future__ import annotations

from enum import StrEnum


class Category(StrEnum):
    """Represent the functional category of an inspection rule."""

    SYSTEM = "system"
    STORAGE = "storage"
    RECORDER = "recorder"
    DATABASE = "database"
    SUPERVISOR = "supervisor"
    CORE = "core"
    OPERATING_SYSTEM = "operating_system"
    FRONTEND = "frontend"
    NETWORK = "network"
    DNS = "dns"
    MQTT = "mqtt"
    ZIGBEE = "zigbee"
    INTEGRATIONS = "integrations"
    ENTITIES = "entities"
    AUTOMATIONS = "automations"
    SCRIPTS = "scripts"
    SECURITY = "security"
    BACKUPS = "backups"
    PERFORMANCE = "performance"
