# HA Inspector release process

This document describes the supported release process for HA Inspector.

## Pre-release validation

Before building a release:

1. Work from a clean release branch based on `main`.
2. Confirm `manifest.json`, `const.py`, README, and CHANGELOG use the same
   integration version.
3. Run Ruff.
4. Run mypy.
5. Run the complete pytest suite.
6. Confirm GitHub Actions passes.
7. Confirm the public API and schema versions are intentional.

## Automated release validation

During development, run the complete automated release-readiness validation with:

    scripts/validate_release.sh

The validator checks version consistency, public API contract versions, Ruff,
mypy, the complete pytest suite with 100% coverage, diff integrity, and the
release archive.

For final release validation, require a clean working tree:

    REQUIRE_CLEAN_TREE=1 scripts/validate_release.sh

Home Assistant deployment validation remains a manual step because it must be
performed against a real Home Assistant installation.

## Real deployment validation

HA Inspector 0.6.0 has been validated on a real Home Assistant OS
installation using the release archive produced by `scripts/build_release.sh`.

The validation covered:

- release archive SHA-256 verification before deployment;
- archive and installed-package integrity (65 source files);
- replacement of an existing HA Inspector 0.6.0 installation without
  requiring Home Assistant reconfiguration;
- successful Home Assistant restart after deployment;
- successful loading of HA Inspector 0.6.0;
- public API version 1, capabilities schema version 1, and result schema
  version 2;
- availability of all four public services;
- discovery of 9 profiles, 26 rules, and 9 collectors;
- successful execution of the `quick`, `pre_upgrade`, and `post_restore`
  profiles without engine execution errors;
- propagation of the latest inspection result to the HA Inspector status
  sensor, including score, health status, finding counts, dashboard summary,
  and domain summaries;
- absence of HA Inspector-specific errors in the Home Assistant log after
  deployment and profile execution.

The validation environment used Home Assistant Core 2026.8.2 on Home
Assistant OS (`generic-x86-64`).

This validates deployment of the 0.6.0 release artifact over an existing
0.6.0 installation. A version-to-version migration must still be validated
when a release introduces configuration-entry or persistent-data migrations.

## Build

Build the release archive with:

    scripts/build_release.sh

The archive is created under:

    dist/ha-inspector-<version>.tar.gz

The archive contains only:

    ha_inspector/

It does not include repository documentation, historical sprint artifacts,
virtual environments, tests, Git metadata, or Python caches.

## Home Assistant deployment validation

Before publishing a release:

1. Back up the currently installed HA Inspector directory.
2. Extract the release under `/config/custom_components`.
3. Restart Home Assistant.
4. Confirm HA Inspector loads without errors.
5. Run `ha_inspector.info`.
6. Confirm the integration version and public API schema versions.
7. Run the `quick` profile.
8. Confirm the HA Inspector status sensor updates.
9. Run the `pre_upgrade` profile.
10. Run the `post_restore` profile.
11. Review the Home Assistant log for HA Inspector errors.

## Release publication

After deployment validation:

1. Merge the release-readiness pull request.
2. Build the archive again from merged `main`.
3. Create the matching Git tag.
4. Publish the GitHub release.
5. Attach the release archive.
6. Verify the published archive installs successfully.

## Compatibility

HA Inspector 0.6.0 keeps public API version 1.

Upgrading from 0.5.1 does not require a configuration-entry migration.
