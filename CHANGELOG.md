# Changelog

## 1.4.2

### Fixed

- Update the `Dependency investigation` diagnostic sensor from the serialized
  inspection findings that Home Assistant actually receives.
- Prevent malformed dependency findings or counter values from breaking
  dependency investigation sensor updates.

### Compatibility

- Public API remains version 1.
- Capabilities schema remains version 1.
- Inspection result schema remains version 2.
- Diagnostic report schema remains version 1.
- No configuration-entry migration is required from 1.4.1.

### Validation

- Ruff passes.
- mypy passes across 81 source files.
- 761 tests pass.
- Python test coverage remains 100%.
- Dependency investigation sensor tests cover live inspection updates and
  malformed finding data.

## 1.4.1

### Fixed

- Advertise the public `ha_inspector.entity_dependency` service through the
  public API description returned by `ha_inspector.info`.

### Compatibility

- Public API remains version 1.
- Capabilities schema remains version 1.
- Inspection result schema remains version 2.
- Diagnostic report schema remains version 1.
- No configuration-entry migration is required from 1.4.0.

### Validation

- Ruff passes.
- mypy passes across 81 source files.
- 760 tests pass.
- Python test coverage remains 100%.
- Public API and `ha_inspector.info` contract tests include
  `entity_dependency`.

## 1.4.0

### Added

- Reverse dependency lookup for individual entities.
- Dependency summaries grouped by automation, script, and scene configuration
  type.
- Classification of active and disabled configuration references.
- Stale-reference investigation context for missing entities.
- Per-entity dependency impact summaries.
- Public `ha_inspector.entity_dependency` response service for live dependency
  queries.
- Dedicated `Dependency investigation` diagnostic sensor in Home Assistant.
- Safe cleanup recommendations for missing entities without automatic
  configuration changes.

### Changed

- Expanded dependency investigation with current automation, script, and scene
  reference details.
- Distinguished active references from disabled-only references when
  investigating stale entity references.
- Added non-destructive cleanup guidance to the entity dependency service.
- Extended Home Assistant-facing dependency diagnostics with missing,
  unreferenced, and disabled-automation context.

### Compatibility

- Public API remains version 1.
- Capabilities schema remains version 1.
- Inspection result schema remains version 2.
- Diagnostic report schema remains version 1.
- No configuration-entry migration is required from 1.3.1.

### Validation

- Ruff passes.
- mypy passes across 81 source files.
- 760 tests pass.
- Python test coverage remains 100%.
- Safe cleanup recommendations never modify Home Assistant configuration
  automatically.
- Release archive/source integrity validation and release-readiness validation
  are required before publication.

## 1.3.1

### Fixed

- Ignore Home Assistant internal entity-registry IDs exposed by device
  conditions when collecting automation, script, and scene dependencies.
- Prevent those internal registry IDs from being reported as missing entity
  references.

### Compatibility

- Public API remains version 1.
- Capabilities schema remains version 1.
- Inspection result schema remains version 2.
- Diagnostic report schema remains version 1.
- No configuration-entry migration is required from 1.3.0.

### Validation

- Regression coverage includes automation, script, scene, and entity collector
  handling of internal entity-registry IDs.
- The fix has been validated against a real Home Assistant installation.
- Ruff passes.
- mypy passes across 76 source files.
- 725 tests pass.
- Python coverage is 100% across 3109 statements.
- Release archive/source integrity validation passes across 80 files.
- Release-readiness validation passes.

## 1.3.0

### Added

- Actionable findings for missing entity references.
- Findings for entities that are not referenced by known configuration sources.
- Dependency health inspection for referenced entities in unavailable or
  unknown states.
- Affected automation, script, and scene summaries for problematic
  dependencies.
- Dependency impact scoring and priority classification.
- Compact dependency diagnostics in entity domain health and dashboard
  summaries.
- Built-in `dependencies` inspection profile.
- Dedicated `Dependency health` diagnostic sensor.
- Public `ha_inspector.dependency_diagnostics` response service.

### Changed

- Expanded entity dependency diagnostics with runtime health and configuration
  impact information.
- Prioritized problematic dependencies by impact score and reference count.
- Extended Home Assistant-facing diagnostics with dependency-specific sensor
  and service output.
- Expanded the built-in inspection profile set from nine to ten profiles.
- Added dependency diagnostics to the stable public service inventory.

### Compatibility

- Public API remains version 1.
- Capabilities schema remains version 1.
- Inspection result schema remains version 2.
- Diagnostic report schema remains version 1.
- No configuration-entry migration is required from 1.2.0.

### Validation

- Ruff passes.
- mypy passes across 76 source files.
- 720 tests pass.
- Python coverage is 100% across 3106 statements.
- Release archive/source integrity validation passes.
- Release-readiness validation passes.

## 1.2.0

### Added

- Entity reference discovery across nested configuration values.
- Automation dependency inspection.
- Script dependency inspection.
- Scene dependency inspection.
- Template and configuration reference inspection.
- Conservative unreferenced entity detection across known dependency sources.
- Missing entity reference detection.
- Per-entity dependency summaries with automation, script, and scene references.

### Changed

- Expanded entity diagnostics with configuration dependency information.
- Added deterministic reverse dependency summaries grouped by referenced entity.
- Distinguished unreferenced entities from entities that can be conclusively
  considered unused.
- Extended entity inspection state with missing-reference and dependency
  summary information.

### Compatibility

- Public API remains version 1.
- Capabilities schema remains version 1.
- Inspection result schema remains version 2.
- Diagnostic report schema remains version 1.
- No configuration-entry migration is required from 1.1.0.

### Validation

- Ruff passes.
- mypy passes across 74 source files.
- 687 tests pass.
- Python coverage is 100% across 2986 statements.
- Release archive/source integrity validation passes across 78 files.
- Release-readiness validation passes.

## 1.1.0

### Added

- Persistent inspection history with compact stored inspection snapshots.
- Health-score and domain-health trend analysis.
- Regression and recovery detection between inspections.
- Historical inspection comparison.
- Configurable rule thresholds.
- Rule acknowledgement and suppression support.
- Inspection, collector, and rule timing metrics.
- Collector failure isolation and reporting.
- Exportable diagnostic reports.
- Richer HA Inspector status sensor attributes.
- Dedicated health-score, findings, and collector-failure diagnostic sensors.
- Dashboard-oriented domain health sensors.
- Improved Home Assistant Repairs integration.
- Complete service response documentation and examples.

### Changed

- Expanded Home Assistant-facing diagnostics for dashboards and operational
  monitoring.
- Improved inspection result presentation with historical and operational
  context.
- Improved Repairs collection and finding reporting.
- Expanded public service documentation for all supported HA Inspector
  services.

### Compatibility

- Public API remains version 1.
- Capabilities schema remains version 1.
- Inspection result schema remains version 2.
- Diagnostic report schema remains version 1.
- No configuration-entry migration is required from 1.0.0.

### Validation

- Ruff passes.
- mypy passes across 67 source files.
- 638 tests pass.
- Python coverage is 100% across 2741 statements.
- Release archive/source integrity validation passes across 71 files.
- Release-readiness validation passes.

## 1.0.0

### Added

- Automated end-to-end release-readiness validation.
- Documented real Home Assistant OS deployment validation.

### Changed

- Enforced 100% Python coverage as a blocking CI requirement.
- Enforced strict mypy validation across the complete integration package.
- Hardened release archive integrity validation.
- Finalized packaging, documentation, and deployment procedures for the
  stable public release.

### Fixed

- Improved backup date compatibility across Home Assistant runtime values.
- Added coverage for defensive collector and persistence branches.

### Compatibility

- Public API remains version 1.
- Capabilities schema remains version 1.
- Inspection result schema remains version 2.
- No configuration-entry migration is required from 0.6.0.

### Validation

- Ruff passes.
- mypy passes across 61 source files.
- 463 tests pass.
- Python coverage is 100%.
- Release archive/source integrity validation passes.
- Real Home Assistant upgrade validation from 0.6.0 completed successfully.

## 0.6.0

### Added

- Automatic collector and rule discovery with typed engine registries.
- Weighted health scoring and category health analytics.
- Comparison between inspection results.
- Storage, backup, Recorder, system, network, integration, entity, add-on,
  log, restart-history, and Home Assistant Repairs inspections.
- User-facing domain health summaries for storage, system, integrations,
  and entities.
- Grouped and severity-ordered presentation results.
- Compact dashboard summary exposed through inspection results and the
  HA Inspector status sensor.
- Built-in `pre_upgrade` and `post_restore` inspection profiles.
- Stable public API version 1 with explicit engine exports.
- Public capability document schema version 1.
- Inspection result schema version 2.
- Public API metadata through `ha_inspector.info`.

### Changed

- Expanded the built-in profile set from seven to nine profiles.
- Improved request filtering by rule ID, category, and tags.
- Extended service responses with health, presentation, dashboard, and
  public API metadata.
- Expanded strict typing coverage across the inspection engine.
- Expanded automated test coverage to 442 tests.
- Kept Ruff, mypy, and Python coverage validation enforced in CI.

### Fixed

- Improved collector and rule execution compatibility across Home Assistant
  runtime states.
- Improved handling of unavailable or unsupported diagnostic sources.
- Preserved stable rule identifiers across profiles and public requests.

### Upgrade from 0.5.1

- No configuration migration is required.
- Existing Home Assistant configuration entries remain valid.
- Existing service names remain unchanged.
- Existing public API version 1 fields remain supported.
- Inspection result schema remains version 2.
- New response fields are additive.
- Restart Home Assistant after replacing the integration files.

### Validation

- Ruff passes.
- mypy passes.
- 442 tests pass.
- Python coverage remains enforced in CI.
- Development and validation use Python 3.14.

## 0.5.1

### Added

- Localized inspection findings and profile descriptions in English and Spanish.
- Profile selector support in the `ha_inspector.run` Home Assistant service.
- Explicit Home Assistant service schemas for `run`, `list_profiles`, `describe_profile`, and `info`.
- Complete project documentation for installation, services, profiles, localization, and development.

### Changed

- Updated the built-in `quick` and `system` profiles to use the current rule registry.
- Expanded `ha_inspector.run` documentation to include profiles and include/exclude filters.
- Enforced 100% Python coverage across the full HA Inspector integration in CI.

### Fixed

- Restored the HA Inspector status sensor and runtime result dispatch.
- Fixed rule execution compatibility between public rule IDs and rule metadata IDs.
- Fixed profile execution failures caused by obsolete rule identifiers.
- Fixed Home Assistant service validation for profile, diagnostics, language, and filter parameters.

### Validation

- Ruff passes.
- mypy passes.
- 351 tests pass.
- Python coverage remains at 100%.
- Validated on Home Assistant Core 2026.8.2.