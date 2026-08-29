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

- [x] Results grouped and ordered for presentation
- [x] Storage, system, integration and entity health summaries
- [x] Pre-upgrade and post-restore profiles
- [x] Dashboard summary
- [x] Localization
- [x] Stable public API

## Epic F — Historical health and trends

- [x] Persist inspection history
- [x] Health-score trend analysis
- [x] Domain-health trend analysis
- [x] Regression and recovery detection
- [x] Historical inspection comparison

## Epic G — Operational diagnostics

- [x] Configurable rule thresholds
- [x] Rule suppression and acknowledgement
- [x] Inspection duration and collector timing metrics
- [x] Collector failure isolation and reporting
- [x] Exportable diagnostic report

## Epic H — Home Assistant integration UX

- [x] Richer status sensor attributes
- [x] Dedicated diagnostic entities
- [x] Dashboard-oriented entity model
- [x] Improved Repairs integration
- [x] Service response documentation and examples

## Epic I — Configuration dependencies

- [x] Entity reference discovery
- [x] Automation dependency inspection
- [x] Script dependency inspection
- [x] Scene dependency inspection
- [x] Template and configuration reference inspection
- [x] Unused entity detection
- [x] Missing entity reference detection
- [x] Entity dependency summaries

## Epic J — Dependency diagnostics and cleanup

- [x] Missing entity reference findings
- [ ] Unreferenced entity findings
- [ ] Dependency health inspection for unavailable and unknown entities
- [ ] Affected configuration summaries
- [ ] Dependency impact scoring and prioritization
- [ ] Dependency diagnostics in domain health and dashboard summary
- [ ] Dependency-focused inspection profile
- [ ] Dependency diagnostics in Home Assistant entities and services

## Version direction

### 0.5 — Engine foundation

Initial engine foundation and Home Assistant integration services.

### 0.6 — Consolidated health inspection release

Storage and recovery, system performance, Home Assistant health,
user-facing summaries, targeted profiles, and stable public API.

### 1.0 — Stable public release

Production release after upgrade-path validation, packaging review,
documentation completion, and real Home Assistant deployment validation.

### 1.1 — Historical health and operational diagnostics

Inspection history, trend and regression analysis, configurable thresholds,
improved operational diagnostics, and richer Home Assistant presentation.

### 1.2 — Configuration dependencies

Entity-reference discovery, configuration dependency analysis, unused entity
detection, missing-reference detection, and dependency-oriented diagnostics.

### 1.3 — Dependency diagnostics and configuration cleanup

Actionable dependency findings, configuration impact analysis, dependency
health scoring, prioritization, and dedicated dependency-focused diagnostics.
