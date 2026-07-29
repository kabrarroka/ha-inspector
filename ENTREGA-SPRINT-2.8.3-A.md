# HA Inspector — Sprint 2.8.3-A

## Objetivo

Añadir una utilidad reutilizable para interpretar versiones de Home Assistant
Core sin introducir todavía una nueva regla de inspección.

## Archivos incluidos

```text
custom_components/ha_inspector/engine/utils/__init__.py
custom_components/ha_inspector/engine/utils/versions.py
tests/test_version_utils.py
```

## API incorporada

```python
VersionKind
VersionInfo
parse_home_assistant_version(version)
```

## Clasificaciones soportadas

| Entrada | Resultado |
|---|---|
| `2026.7.2` | `STABLE` |
| `2026.8.0b3` | `BETA` |
| `2026.8.0rc2` | `RC` |
| `2026.8.0.dev0` | `DEV` |
| `None`, vacío o formato inválido | `UNKNOWN` |

## Aplicación

Copia el contenido del ZIP en la raíz del repositorio, conservando las rutas.

## Pruebas

Desde la raíz del proyecto:

```bash
pytest -q
```

También puedes ejecutar únicamente esta entrega:

```bash
pytest -q tests/test_version_utils.py
```

## Commit sugerido

```bash
git add custom_components/ha_inspector/engine/utils tests/test_version_utils.py
git commit -m "Sprint 2.8.3-A: add Home Assistant version parser"
```

## Siguiente entrega

Sprint 2.8.3-B:

- nueva regla `CoreVersionRule`
- uso de este parser
- findings INFO para beta, RC y dev
- WARNING para versión ausente o inválida
