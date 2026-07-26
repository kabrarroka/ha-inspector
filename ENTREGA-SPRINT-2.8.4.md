# HA Inspector — Sprint 2.8.4

## Objetivo

Añadir `SupervisorVersionRule` reutilizando el parser de versiones del
Sprint 2.8.3-A.

## Decisión importante

La ausencia de versión del Supervisor **no genera un Finding** en esta regla.

Ese caso ya pertenece a `SupervisorAvailabilityRule`, que decide si el
Supervisor debería existir según el tipo de instalación. De esta forma se
evitan dos avisos por el mismo problema.

## Comportamiento

| Valor de `supervisor_version` | Resultado |
|---|---|
| `2026.07.3` | Sin Findings |
| `2026.8.0b2` | INFO — Supervisor beta |
| `2026.8.0rc1` | INFO — Supervisor release candidate |
| `2026.8.0.dev0` | INFO — Supervisor development |
| `None`, vacío o espacios | Sin Findings |
| Valor presente pero inválido | WARNING — versión indeterminada |

## Archivos

```text
custom_components/ha_inspector/engine/rules/supervisor_version.py
tests/test_supervisor_version_rule.py
```

## Registro

En el archivo donde se importan o instancian las reglas, añade:

```python
from .rules.supervisor_version import SupervisorVersionRule
```

y registra:

```python
SupervisorVersionRule()
```

Colócala después de `SupervisorAvailabilityRule`.

## Pruebas

```powershell
python -m pytest -q
```

Prueba aislada:

```powershell
python -m pytest -q tests/test_supervisor_version_rule.py
```

## Commit sugerido

```powershell
git add custom_components/ha_inspector/engine/rules/supervisor_version.py tests/test_supervisor_version_rule.py
git commit -m "Sprint 2.8.4: add Supervisor version rule"
git push
```
