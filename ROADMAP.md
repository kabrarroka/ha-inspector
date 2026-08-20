# HA Inspector Roadmap

This roadmap is a living guide for the project. Priorities may change as
Home Assistant evolves and new diagnostic needs are identified.

## Epic A — Core engine

- [x] Automatic collector and rule discovery
- [x] Rule descriptors and categories
- [x] Rule registry and selector
- [x] Inspection execution plans
- [x] Inspection profiles
- [x] Weighted health score
- [x] Category health analytics
- [x] Comparison between inspection results

## Epic B — Storage and recovery health

- [x] Disk free-space inspection
- [x] Backup count inspection
- [x] Backup age inspection
- [x] Backup agent availability
- [x] Recorder database-size inspection
- [x] Log error and warning inspection

## Epic C — System health

- [x] CPU-load inspection
- [x] Memory-usage inspection
- [x] Restart-frequency inspection
- [x] Time-synchronization inspection
- [x] DNS and network-connectivity inspection

## Epic D — Home Assistant health

- [x] Core, Frontend, Supervisor and OS version inventory
- [x] Supervisor and Recorder availability
- [x] Integration setup, retry and lifecycle errors
- [x] Unavailable and unknown entities
- [x] Duplicate entity names
- [x] Disabled automation inventory
- [x] Add-on health
- [x] Repair issue inspection

## Epic E — User experience

- [ ] Results grouped and ordered for presentation
- [ ] Storage, system, integration and entity health summaries
- [ ] Pre-upgrade and post-restore profiles
- [ ] Dashboard summary
- [x] Localization
- [ ] Stable public API

## Version direction

### 0.5 — Engine foundation

Core discovery, selection, profiles, scoring and analytics.

### 0.6 — Storage and recovery

Disk, backup and Recorder health checks.

### 0.7 — System performance

CPU, memory, logs and restart diagnostics.

### 0.8 — User-facing health summaries

Health domains, presentation and targeted profiles.

### 1.0 — Stable public release

Stable API, complete documentation and supported upgrade path.
