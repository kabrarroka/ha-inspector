"""Built-in rule metadata catalog."""

from __future__ import annotations

from ..category import Category
from ..descriptors import RuleDescriptor

RULE_DESCRIPTORS: dict[str, RuleDescriptor] = {
    "SYSTEM_INFORMATION": RuleDescriptor(
        rule_id="system.information",
        category=Category.SYSTEM,
        title="System information",
        description="Collects general information about the Home Assistant installation.",
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
        description="Checks whether the Home Assistant storage has sufficient free space.",
        weight=30,
        tags=("storage", "disk", "health", "availability"),
    ),
}
