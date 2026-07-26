# HA Inspector — Sprint 2.8.3-B

## Objetivo

Añadir `CoreVersionRule`, la primera regla que utiliza el parser de versiones
creado en el Sprint 2.8.3-A.

## Archivos incluidos

```text
custom_components/ha_inspector/engine/rules/core_version.py
tests/test_core_version_rule.py
```

## Comportamiento

| Versión | Resultado |
|---|---|
| `2026.7.2` | Sin hallazgos |
| `2026.8.0b3` | INFO — Running a beta version |
| `2026.8.0rc2` | INFO — Running a release candidate |
| `2026.8.0.dev0` | INFO — Running a development version |
| Vacía, `None` o inválida | WARNING — Unable to determine Core version |

## Aplicación

Descomprime el ZIP en la raíz del repositorio conservando las rutas.

## Registro de la regla

La entrega no sobrescribe el catálogo de reglas porque su ubicación puede variar
según la rama. En el archivo donde se registran o instancian las reglas, importa:

```python
from .rules.core_version import CoreVersionRule
```

y añade:

```python
CoreVersionRule()
```

Si tu catálogo utiliza `RuleDescriptor`, añade también un descriptor para:

```text
system.core_version
```

asociado a `CoreVersionRule`.

## Pruebas

```powershell
python -m pytest -q
```

Para ejecutar solo esta entrega:

```powershell
python -m pytest -q tests/test_core_version_rule.py
```

## Commit sugerido

```powershell
git add custom_components/ha_inspector/engine/rules/core_version.py tests/test_core_version_rule.py
git commit -m "Sprint 2.8.3-B: add Core version rule"
git push
```
