"""Built-in rule metadata catalog."""

from __future__ import annotations

from ..category import Category
from ..descriptors import RuleDescriptor

RULE_DESCRIPTORS: dict[str, RuleDescriptor] = {
    "TIME_SYNCHRONIZATION": RuleDescriptor(
        rule_id="system.time_synchronization",
        category=Category.SYSTEM,
        title="Time synchronization",
        description=(
            "Checks whether the Home Assistant host clock is synchronized."
        ),
        weight=30,
        tags=("system", "time", "ntp", "health"),
    ),
    "RESTART_FREQUENCY": RuleDescriptor(
        rule_id="system.restart_frequency",
        category=Category.SYSTEM,
        title="Restart frequency",
        description=(
            "Checks whether Home Assistant is restarting too frequently."
        ),
        weight=25,
        tags=("system", "restart", "stability", "health"),
    ),
    "MEMORY_USAGE": RuleDescriptor(
        rule_id="system.memory_usage",
        category=Category.SYSTEM,
        title="Memory usage",
        description="Checks whether host memory usage is excessively high.",
        weight=25,
        tags=("system", "memory", "performance", "health"),
    ),
    "CPU_LOAD": RuleDescriptor(
        rule_id="system.cpu_load",
        category=Category.SYSTEM,
        title="CPU load",
        description="Checks whether host CPU usage is excessively high.",
        weight=25,
        tags=("system", "cpu", "performance", "health"),
    ),
    "SYSTEM_INFORMATION": RuleDescriptor(
        rule_id="system.information",
        category=Category.SYSTEM,
        title="System information",
        description=(
            "Collects general information about the Home Assistant installation."
        ),
        weight=0,
        tags=("system", "inventory"),
    ),
    "RECORDER_AVAILABILITY": RuleDescriptor(
        rule_id="recorder.availability",
        category=Category.RECORDER,
        title="Recorder availability",
        description="Checks that Recorder and its database are operational.",
        weight=35,
        tags=("recorder", "database", "availability"),
    ),
    "RECORDER_KEEP_DAYS": RuleDescriptor(
        rule_id="recorder.keep_days",
        category=Category.RECORDER,
        title="Recorder retention period",
        description="Checks whether detailed history retention may be excessive.",
        weight=10,
        tags=("recorder", "database", "performance"),
    ),
    "RECORDER_DATABASE_SIZE": RuleDescriptor(
        rule_id="recorder.database_size",
        category=Category.RECORDER,
        title="Recorder database size",
        description="Checks whether the Recorder database has grown excessively.",
        weight=20,
        tags=("recorder", "database", "storage", "performance"),
    ),
    "INTEGRATION_SETUP_ERRORS": RuleDescriptor(
        rule_id="integrations.setup_error",
        category=Category.INTEGRATIONS,
        title="Integration setup errors",
        description="Detects integrations that failed during setup.",
        weight=25,
        tags=("integrations", "setup", "errors"),
    ),
    "INTEGRATION_SETUP_RETRIES": RuleDescriptor(
        rule_id="integrations.setup_retry",
        category=Category.INTEGRATIONS,
        title="Integration setup retries",
        description="Detects integrations waiting for an automatic retry.",
        weight=12,
        tags=("integrations", "setup", "retry"),
    ),
    "INTEGRATION_LIFECYCLE_ERRORS": RuleDescriptor(
        rule_id="integrations.lifecycle_error",
        category=Category.INTEGRATIONS,
        title="Integration lifecycle errors",
        description="Detects migration and unload failures.",
        weight=20,
        tags=("integrations", "migration", "unload"),
    ),
    "UNAVAILABLE_ENTITIES": RuleDescriptor(
        rule_id="entities.unavailable",
        category=Category.ENTITIES,
        title="Unavailable entities",
        description="Checks whether too many entities are unavailable.",
        weight=15,
        tags=("entities", "availability"),
    ),
    "UNKNOWN_ENTITIES": RuleDescriptor(
        rule_id="entities.unknown",
        category=Category.ENTITIES,
        title="Unknown entities",
        description="Checks whether too many entities have an unknown state.",
        weight=10,
        tags=("entities", "state"),
    ),
    "DUPLICATE_ENTITY_NAMES": RuleDescriptor(
        rule_id="entities.duplicate_names",
        category=Category.ENTITIES,
        title="Duplicate entity names",
        description="Detects friendly names shared by multiple entities.",
        weight=5,
        tags=("entities", "naming", "usability"),
    ),
    "ENTITIES_WITHOUT_AREA": RuleDescriptor(
        rule_id="entities.without_area",
        category=Category.ENTITIES,
        title="Entities without an assigned area",
        description=(
            "Detects entities that do not have an effective area assignment."
        ),
        weight=0,
        tags=("entities", "areas", "organization", "inventory"),
    ),
    "DISABLED_AUTOMATIONS": RuleDescriptor(
        rule_id="automations.disabled",
        category=Category.AUTOMATIONS,
        title="Disabled automations",
        description="Detects automation entities disabled in the entity registry.",
        weight=0,
        tags=("automations", "maintenance", "inventory"),
    ),
    "DISK_FREE_SPACE": RuleDescriptor(
        rule_id="storage.disk_free_space",
        category=Category.STORAGE,
        title="Disk free space",
        description=(
            "Checks whether the Home Assistant storage has sufficient free space."
        ),
        weight=30,
        tags=("storage", "disk", "health", "availability"),
    ),
    "BACKUP_COUNT": RuleDescriptor(
        rule_id="storage.backup_count",
        category=Category.STORAGE,
        title="Backup count",
        description="Checks whether enough Home Assistant backups are available.",
        weight=30,
        tags=("storage", "backups", "recovery", "availability"),
    ),
    "BACKUP_AGE": RuleDescriptor(
        rule_id="storage.backup_age",
        category=Category.STORAGE,
        title="Backup age",
        description="Checks whether the newest Home Assistant backup is recent enough.",
        weight=30,
        tags=("storage", "backups", "recovery", "age"),
    ),
    "BACKUP_AGENT_ERRORS": RuleDescriptor(
        rule_id="storage.backup_agent_errors",
        category=Category.STORAGE,
        title="Backup agent errors",
        description="Checks whether backup agents returned errors.",
        weight=20,
        tags=("storage", "backups", "recovery", "agents"),
    ),
    "BACKUP_REDUNDANCY": RuleDescriptor(
        rule_id="storage.backup_redundancy",
        category=Category.STORAGE,
        title="Backup redundancy",
        description="Checks whether the newest backup exists in multiple locations.",
        weight=25,
        tags=("storage", "backups", "recovery", "redundancy"),
    ),
    "BACKUP_INTEGRITY": RuleDescriptor(
        rule_id="storage.backup_integrity",
        category=Category.STORAGE,
        title="Backup integrity",
        description=(
            "Checks whether the newest backup contains failed components "
            "or storage targets."
        ),
        weight=35,
        tags=("storage", "backups", "recovery", "integrity"),
    ),
}
