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
