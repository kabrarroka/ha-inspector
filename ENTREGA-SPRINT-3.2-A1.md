# HA Inspector — Sprint 3.2 A1

Adds backup inventory collection and the `BACKUP_COUNT` inspection rule.

## Included

- `InspectionContext.backups`.
- `BackupCollector` using Home Assistant's backup manager.
- Unique backup count with newest and oldest dates.
- Backup-agent error summary without exposing exception details.
- `BackupCountRule`.
- `storage.backup_count` descriptor.
- Backup context in diagnostics.
- Collector and rule tests.
- Initial `ROADMAP.md`.

## Behavior

- 3 or more backups: healthy.
- 1 or 2 backups: warning.
- 0 backups: error.
- Backup manager unavailable or invalid data: no false finding.

## Apply

Extract this ZIP at the repository root and allow existing files to be
replaced. Then run:

```bash
git switch main
git pull
git switch -c sprint-3.2-backup-count

python -m pytest
```

## Suggested commit

```bash
git add .
git commit -m "feat(backups): add backup count inspection"
git push -u origin sprint-3.2-backup-count
```
