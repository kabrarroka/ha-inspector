"""Built-in rule metadata catalog."""

from __future__ import annotations

from ..descriptors import RuleDescriptor

RULE_DESCRIPTORS: dict[str, RuleDescriptor] = {
    "SYSTEM_INFORMATION": RuleDescriptor(
        rule_id="system.information",
        category="system",
        title="System information",
        description="Collects general information about the Home Assistant installation.",
        weight=0,
        tags=("system", "inventory"),
    ),
    "OPERATING_SYSTEM_VERSION": RuleDescriptor(
        rule_id="system.operating_system_version",
        category="system",
        title="Home Assistant OS version",
        description=(
            "Checks whether the installed Home Assistant OS version is "
            "stable and uses a recognizable version format."
        ),
        weight=5,
        tags=("system", "version", "operating-system"),
    ),
    "RECORDER_AVAILABILITY": RuleDescriptor(
        rule_id="recorder.availability",
        category="recorder",
        title="Recorder availability",
        description="Checks that Recorder and its database are operational.",
        weight=35,
        tags=("recorder", "database", "availability"),
    ),
    "RECORDER_KEEP_DAYS": RuleDescriptor(
        rule_id="recorder.keep_days",
        category="recorder",
        title="Recorder retention period",
        description="Checks whether detailed history retention may be excessive.",
        weight=10,
        tags=("recorder", "database", "performance"),
    ),
    "INTEGRATION_SETUP_ERRORS": RuleDescriptor(
        rule_id="integrations.setup_error",
        category="integrations",
        title="Integration setup errors",
        description="Detects integrations that failed during setup.",
        weight=25,
        tags=("integrations", "setup", "errors"),
    ),
    "INTEGRATION_SETUP_RETRIES": RuleDescriptor(
        rule_id="integrations.setup_retry",
        category="integrations",
        title="Integration setup retries",
        description="Detects integrations waiting for an automatic retry.",
        weight=12,
        tags=("integrations", "setup", "retry"),
    ),
    "INTEGRATION_LIFECYCLE_ERRORS": RuleDescriptor(
        rule_id="integrations.lifecycle_error",
        category="integrations",
        title="Integration lifecycle errors",
        description="Detects migration and unload failures.",
        weight=20,
        tags=("integrations", "migration", "unload"),
    ),
    "UNAVAILABLE_ENTITIES": RuleDescriptor(
        rule_id="entities.unavailable",
        category="entities",
        title="Unavailable entities",
        description="Checks whether too many entities are unavailable.",
        weight=15,
        tags=("entities", "availability"),
    ),
    "UNKNOWN_ENTITIES": RuleDescriptor(
        rule_id="entities.unknown",
        category="entities",
        title="Unknown entities",
        description="Checks whether too many entities have an unknown state.",
        weight=10,
        tags=("entities", "state"),
    ),
    "DUPLICATE_ENTITY_NAMES": RuleDescriptor(
        rule_id="entities.duplicate_names",
        category="entities",
        title="Duplicate entity names",
        description="Detects friendly names shared by multiple entities.",
        weight=5,
        tags=("entities", "naming", "usability"),
    ),
    "DISABLED_AUTOMATIONS": RuleDescriptor(
        rule_id="automations.disabled",
        category="automations",
        title="Disabled automations",
        description="Detects automation entities disabled in the entity registry.",
        weight=0,
        tags=("automations", "maintenance", "inventory"),
    ),
    "SUPERVISOR_AVAILABILITY": RuleDescriptor(
        rule_id="system.supervisor_availability",
        category="system",
        title="Supervisor availability",
        description=(
        "Checks whether Supervisor information is available for "
        "installation types that require it."
        ),
        weight=20,
        tags=("system", "supervisor", "availability"),
    ),
    "CORE_VERSION": RuleDescriptor(
        rule_id="system.core_version",
        category="system",
        title="Home Assistant Core version",
        description=(
            "Checks whether the installed Home Assistant Core version is "
            "stable and uses a recognizable version format."
        ),
        weight=5,
        tags=("system", "version", "core"),
    ),
    "SUPERVISOR_VERSION": RuleDescriptor(
        rule_id="system.supervisor_version",
        category="system",
        title="Supervisor version",
        description=(
            "Checks whether the installed Home Assistant Supervisor version "
            "is stable and uses a recognizable version format."
        ),
        weight=5,
        tags=("system", "version", "supervisor"),
    ),
    "OPERATING_SYSTEM_VERSION": RuleDescriptor(
        rule_id="system.operating_system_version",
        category="system",
        title="Home Assistant OS version",
        description=(
            "Checks whether the installed Home Assistant OS version is "
            "stable and uses a recognizable version format."
        ),
        weight=5,
        tags=("system", "version", "operating-system"),
    ),
    "INSTALLATION_CONSISTENCY": RuleDescriptor(
        rule_id="system.installation_consistency",
        category="system",
        title="Installation consistency",
        description=(
            "Checks whether the installation type is consistent with the "
            "reported Supervisor and Home Assistant OS components."
        ),
        weight=20,
        tags=("system", "installation", "consistency"),
    ),
}
