# Changelog

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