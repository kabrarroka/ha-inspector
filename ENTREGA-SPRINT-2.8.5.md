# HA Inspector — Sprint 2.8.5

## Objetivo

Añadir soporte correcto para versiones de Home Assistant OS y crear
`OperatingSystemVersionRule`.

## Motivo de la ampliación

El parser existente reconoce versiones de Core y Supervisor, como:

```text
2026.7.2
2026.8.0b3
```

Home Assistant OS utiliza otro esquema:

```text
18.1
17.3.rc1
```

Por eso se añade una función específica:

```python
parse_home_assistant_os_version(...)
```

No se relaja el parser existente, evitando que formatos de componentes
diferentes se mezclen accidentalmente.

## Archivos

```text
custom_components/ha_inspector/engine/utils/versions.py
custom_components/ha_inspector/engine/rules/operating_system_version.py
tests/test_version_utils.py
tests/test_operating_system_version_rule.py
```

`versions.py` y `test_version_utils.py` sustituyen los archivos del Sprint
2.8.3-A conservando todos sus comportamientos anteriores.

## Comportamiento de la regla

| `operating_system_version` | Resultado |
|---|---|
| `18.1` | Sin Findings |
| `18.0.beta2` | INFO |
| `17.3.rc1` | INFO |
| `18.0.dev0` | INFO |
| Vacía o ausente | Sin Findings |
| Presente pero inválida | WARNING |

La ausencia no se considera error porque `Container` y `Core` no ejecutan
Home Assistant OS.

## Registro

Importa:

```python
from .rules.operating_system_version import OperatingSystemVersionRule
```

y registra:

```python
OperatingSystemVersionRule()
```

Colócala después de `SupervisorVersionRule`.

## Pruebas

```powershell
python -m pytest -q
```

Prueba aislada:

```powershell
python -m pytest -q tests/test_version_utils.py tests/test_operating_system_version_rule.py
```

## Commit sugerido

```powershell
git add .
git commit -m "Sprint 2.8.5: add Home Assistant OS version rule"
git push
```
