# HA Inspector

HA Inspector is a custom integration for Home Assistant that inspects a Home Assistant installation and reports configuration, availability, storage, recorder, integration, and entity-related findings.

Current version: **1.3.1**

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

All HA Inspector services return a response and can be used with
`response_variable` in Home Assistant scripts and automations.

### `ha_inspector.run`

Runs the active collectors and inspection rules and returns the complete
serialized inspection result.

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

If `language` is omitted, the configured Home Assistant language is used
when available.

Example:

```yaml
action: ha_inspector.run
data:
  profile: quick
  diagnostics: true
  language: es
response_variable: inspection
```

Typical response fields include:

```yaml
schema_version: 2
score: 100
total_findings: 0
findings: []
health: {}
summary: {}
health_summary: {}
domain_health: {}
dashboard_summary: {}
metadata:
  profile: quick
  language: es
```

The exact result structure is defined by Inspection Result schema version 2.

### `ha_inspector.list_profiles`

Returns the available built-in inspection profiles.

```yaml
action: ha_inspector.list_profiles
response_variable: profiles_response
```

Response shape:

```yaml
profiles:
  - profile_id: quick
    title: Quick inspection
    description: ...
```

Each entry contains `profile_id`, `title`, and `description`.

### `ha_inspector.describe_profile`

Returns the complete definition of one inspection profile.

Required field:

- `profile_id`: profile identifier.

Example:

```yaml
action: ha_inspector.describe_profile
data:
  profile_id: quick
response_variable: profile_response
```

Response shape:

```yaml
profile:
  profile_id: quick
  title: Quick inspection
  description: ...
  request:
    include_rule_ids: []
    include_categories: []
    include_tags: []
    exclude_rule_ids: []
    exclude_categories: []
    exclude_tags: []
    diagnostics: false
```

The exact `request` values depend on the selected profile.

### `ha_inspector.info`

Returns integration version, public API information, schema versions, supported
services, and engine information.

```yaml
action: ha_inspector.info
response_variable: inspector_info
```

Response shape:

```yaml
version: 1.3.1
api_version: 1
public_api:
  api_version: 1
  schemas:
    capabilities: 1
    result: 2
  services:
    - run
    - list_profiles
    - describe_profile
    - info
    - list_acknowledgements
    - acknowledge_finding
    - clear_acknowledgement
    - clear_acknowledgements
    - export_diagnostic_report
    - dependency_diagnostics
engine: {}
```

The `engine` section reports the current engine capabilities and discovered
components.

### `ha_inspector.list_acknowledgements`

Returns the finding IDs that are persistently acknowledged and suppressed from
future inspection results and health scoring.

```yaml
action: ha_inspector.list_acknowledgements
response_variable: acknowledgements
```

Response shape:

```yaml
finding_ids:
  - BACKUP_AGE_HIGH
  - UNAVAILABLE_ENTITIES_EXCESSIVE
count: 2
```

### `ha_inspector.acknowledge_finding`

Persistently acknowledges one finding.

Required field:

- `finding_id`: exact finding identifier.

```yaml
action: ha_inspector.acknowledge_finding
data:
  finding_id: UNAVAILABLE_ENTITIES_EXCESSIVE
response_variable: acknowledgements
```

Response shape:

```yaml
finding_ids:
  - UNAVAILABLE_ENTITIES_EXCESSIVE
count: 1
```

The response always contains the complete updated acknowledgement state.

### `ha_inspector.clear_acknowledgement`

Removes one persisted acknowledgement.

Required field:

- `finding_id`: exact finding identifier.

```yaml
action: ha_inspector.clear_acknowledgement
data:
  finding_id: UNAVAILABLE_ENTITIES_EXCESSIVE
response_variable: acknowledgements
```

The response contains the complete updated acknowledgement state.

### `ha_inspector.clear_acknowledgements`

Removes every persisted acknowledgement.

```yaml
action: ha_inspector.clear_acknowledgements
response_variable: acknowledgements
```

Response after all acknowledgements have been cleared:

```yaml
finding_ids: []
count: 0
```

### `ha_inspector.dependency_diagnostics`

Returns the compact dependency diagnostics from the most recent inspection.

The service does not run a new inspection. Before any inspection has completed,
it returns a stable empty summary.

```yaml
action: ha_inspector.dependency_diagnostics
response_variable: dependency_diagnostics
```

Response shape:

```yaml
affected_entities: 4
unavailable: 2
unknown: 2
critical: 1
high: 1
medium: 1
low: 1
max_impact_score: 55
```

The same compact dependency information is also exposed by the dedicated
`Dependency health` diagnostic sensor.

### `ha_inspector.export_diagnostic_report`

Returns an exportable diagnostic report built from the most recent inspection.

Run `ha_inspector.run` at least once before calling this service.

```yaml
action: ha_inspector.export_diagnostic_report
response_variable: diagnostic_report
```

Top-level response shape:

```yaml
schema_version: 1
generator:
  name: HA Inspector
  version: 1.3.1
inspection:
  schema_version: 2
  started_at: ...
  finished_at: ...
  duration_seconds: ...
  checks_executed: ...
  total_findings: ...
  score: ...
  health: ...
  summary: ...
  health_summary: ...
  domain_health: ...
  dashboard_summary: ...
findings: []
operational:
  profile: quick
  language: en
  diagnostics_included: false
  collectors_executed: ...
  collectors_succeeded: ...
  collectors_failed: ...
  collector_errors: ...
  rules_discovered: ...
  rules_selected: ...
  timings: ...
  suppressed_findings_count: ...
```

The report contains a controlled operational subset rather than the unfiltered
diagnostic context.


## Built-in profiles

HA Inspector currently provides ten inspection profiles.

| Profile | Purpose |
| --- | --- |
| `full` | Run every registered inspection rule |
| `quick` | Run a reduced set of high-value system and availability checks |
| `system` | Inspect Home Assistant system and platform information |
| `entities` | Inspect entity availability, state, and naming |
| `dependencies` | Inspect configuration dependencies, missing references, and problematic referenced entities |
| `integrations` | Inspect integration setup and lifecycle errors |
| `post_restore` | Check service health after restoring a backup |
| `pre_upgrade` | Check recovery readiness before upgrading |
| `recorder` | Inspect recorder availability and retention settings |
| `storage` | Inspect storage availability and free disk space |


## Public API

HA Inspector exposes public API version **1**.

The stable public contract includes:

- Home Assistant services: `run`, `list_profiles`, `describe_profile`, `info`, `list_acknowledgements`, `acknowledge_finding`, `clear_acknowledgement`, `clear_acknowledgements`, `export_diagnostic_report`, and `dependency_diagnostics`.
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


## Upgrading

To upgrade from HA Inspector 0.6.0 to 1.0.0:

1. Replace the existing `custom_components/ha_inspector` directory with the
   1.0.0 files.
2. Keep the existing Home Assistant configuration entry.
3. Restart Home Assistant.
4. Confirm that HA Inspector loads without errors.
5. Run `ha_inspector.info` and verify:
   - integration version `1.0.0`;
   - public API version `1`;
   - capabilities schema version `1`;
   - result schema version `2`.
6. Run the `quick` inspection profile and confirm the status sensor updates.
7. Run the `pre_upgrade` and `post_restore` profiles as appropriate.

No configuration-entry migration is required for this release.

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

Current integration version: **1.3.1**

The project maintains 100% Python test coverage across `custom_components.ha_inspector`.

## Repository

https://github.com/kabrarroka/ha-inspector
