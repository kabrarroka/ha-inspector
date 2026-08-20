# Changelog

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