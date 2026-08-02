# HA Inspector — Sprint 3.1 A1

Primera entrega funcional de `DISK_FREE_SPACE`.

## Incluye

- Nueva regla `DiskFreeSpaceRule`.
- Descriptor `storage.disk_free_space`.
- Migración del catálogo actual a `Category`.
- Umbral de aviso: menos del 20 % libre.
- Umbral de error: menos del 10 % libre.
- Pruebas de estado saludable, aviso, error, límites y datos inválidos.

## Aplicación

Descomprime el ZIP en la raíz del repositorio y permite reemplazar
`custom_components/ha_inspector/engine/rules/catalog.py`.

Después ejecuta:

```bash
git switch main
git pull
git switch -c sprint-3.1-disk-free-space

python -m pytest
```

## Commit sugerido

```bash
git add .
git commit -m "feat(storage): add disk free space inspection rule"
git push -u origin sprint-3.1-disk-free-space
```
