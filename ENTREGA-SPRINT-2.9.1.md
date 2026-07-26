# HA Inspector — Sprint 2.9.1

## Objetivo

Añadir `InstallationConsistencyRule`, la primera regla que relaciona varios
datos del sistema en vez de validarlos por separado.

## Matriz aplicada

| Instalación | Supervisor | HAOS |
|---|---:|---:|
| Home Assistant OS | esperado | esperado |
| Supervised | esperado | no esperado |
| Container | no esperado | no esperado |
| Core | no esperado | no esperado |

## Evitar duplicados

La ausencia del Supervisor en HAOS o Supervised continúa siendo
responsabilidad de `SupervisorAvailabilityRule`.

`InstallationConsistencyRule` no repite ese Finding.

## Normalización

La regla acepta variantes como:

```text
Home Assistant OS
HA OS
HAOS
Home Assistant Supervised
Supervised
Home Assistant Container
Container
Home Assistant Core
Core
```

También tolera diferencias de mayúsculas, guiones y guiones bajos.

## Archivos

```text
custom_components/ha_inspector/engine/rules/installation_consistency.py
tests/test_installation_consistency_rule.py
```

## Catálogo

Añade a `RULE_DESCRIPTORS`:

```python
"INSTALLATION_CONSISTENCY": RuleDescriptor(
    rule_id="system.installation_consistency",
    category="system",
    title="Installation consistency",
    description=(
        "Checks whether the installation type is consistent with the "
        "reported Supervisor and Home Assistant OS components."
    ),
    weight=20,
    tags=("system", "installation", "consistency"),
),
```

No instancies la regla: `discovery.py` la detectará automáticamente.

## Pruebas

```powershell
python -m pytest -q
```

Prueba aislada:

```powershell
python -m pytest -q tests/test_installation_consistency_rule.py
```

## Commit sugerido

```powershell
git add .
git commit -m "Sprint 2.9.1: add installation consistency rule"
git push
```
