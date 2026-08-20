# HA Inspector

HA Inspector is a custom integration for Home Assistant that inspects a Home Assistant installation and reports configuration, availability, storage, recorder, integration, and entity-related findings.

Current version: **0.5.1**

## Features

- Inspection engine based on reusable collectors and rules.
- Built-in inspection profiles.
- Home Assistant services for running inspections and querying the engine.
- Status sensor updated after every inspection.
- Optional diagnostic context in inspection responses.
- Localized findings, recommendations, and profiles.
- English and Spanish support.
- Configuration through the Home Assistant UI.
- 100% Python test coverage enforced in CI.

## Installation

Copy the directory:

```text
custom_components/ha_inspector
```

to:

```text
/config/custom_components/ha_inspector
```

Restart Home Assistant.

Then go to **Settings → Devices & services → Add integration**, search for **HA Inspector**, and complete the configuration flow.

HA Inspector supports a single configuration entry.

## Status sensor

HA Inspector provides a sensor containing the status of the most recent inspection. The sensor is updated whenever an inspection finishes.

Possible states are:

- `critical`
- `error`
- `warning`
- `info`
- `ok`

## Services

### `ha_inspector.run`

Runs the active collectors and inspection rules and returns the complete inspection result.

Optional fields:

- `profile`: Built-in inspection profile to use as the base configuration.
- `include_rule_ids`: Run only the specified rule IDs.
- `include_categories`: Run rules from the specified categories.
- `include_tags`: Run rules matching the specified tags.
- `exclude_rule_ids`: Exclude the specified rule IDs.
- `exclude_categories`: Exclude rules from the specified categories.
- `exclude_tags`: Exclude rules matching the specified tags.
- `diagnostics`: Include the collected technical diagnostic context.
- `language`: Language for findings and recommendations (`en` or `es`).

Explicit service fields override the values provided by a profile.

If `language` is omitted, the configured Home Assistant language is used when available.

Example:

```yaml
action: ha_inspector.run
data:
  profile: quick
  diagnostics: true
  language: es
response_variable: inspection
```

### `ha_inspector.list_profiles`

Returns the available built-in inspection profiles.

```yaml
action: ha_inspector.list_profiles
response_variable: profiles
```

### `ha_inspector.describe_profile`

Returns the complete definition of an inspection profile.

Required field:

- `profile_id`: profile identifier.

Example:

```yaml
action: ha_inspector.describe_profile
data:
  profile_id: quick
response_variable: profile
```

### `ha_inspector.info`

Returns information about the HA Inspector engine.

```yaml
action: ha_inspector.info
response_variable: inspector_info
```

## Built-in profiles

HA Inspector currently provides nine inspection profiles.

| Profile | Purpose |
| --- | --- |
| `full` | Run every registered inspection rule |
| `quick` | Run a reduced set of high-value system and availability checks |
| `system` | Inspect Home Assistant system and platform information |
| `entities` | Inspect entity availability, state, and naming |
| `integrations` | Inspect integration setup and lifecycle errors |
| `post_restore` | Check service health after restoring a backup |
| `pre_upgrade` | Check recovery readiness before upgrading |
| `recorder` | Inspect recorder availability and retention settings |
| `storage` | Inspect storage availability and free disk space |


## Public API

HA Inspector exposes public API version **1**.

The stable public contract includes:

- Home Assistant services: `run`, `list_profiles`, `describe_profile`, and `info`.
- `InspectionRequest` for inspection request configuration.
- `InspectionResult` and its serialized result document.
- `Finding` and `Severity`.
- `EngineCapabilities` and the capabilities document.
- Built-in profile discovery through `get_profile()` and `list_profiles()`.

Current schema versions:

| Contract | Version |
| --- | ---: |
| Public API | 1 |
| Capabilities document | 1 |
| Inspection result | 2 |

`ha_inspector.info` reports the public API version, schema versions, and
supported service names.

Within public API version 1, existing fields and service names are preserved.
New optional fields may be added without changing the public API version.
Breaking changes require a new public API version.

## Localization

HA Inspector currently supports English (`en`) and Spanish (`es`).

Inspection findings, recommendations, and profile descriptions can be localized.

When no explicit language is supplied, HA Inspector uses the Home Assistant language when possible and otherwise falls back to English.

## Development

Development requires Python 3.14.

Create and activate a virtual environment and install the development dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

Run the complete validation suite:

```bash
ruff check custom_components/ha_inspector tests
python -m mypy
pytest \
  --cov=custom_components.ha_inspector \
  --cov-report=term-missing \
  --cov-fail-under=100
```

GitHub Actions runs Ruff, mypy, and pytest for pushes and pull requests.

## Project status

HA Inspector is under active development.

Current integration version: **0.5.1**

The project maintains 100% Python test coverage across `custom_components.ha_inspector`.

## Repository

https://github.com/kabrarroka/ha-inspector
