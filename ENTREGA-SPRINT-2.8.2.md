# HA Inspector — Sprint 2.8.2

## Incluye

- Nueva regla `SupervisorAvailabilityRule`.
- Detecta Supervisor ausente en:
  - Home Assistant OS
  - Home Assistant Supervised
- No genera falsos positivos en:
  - Home Assistant Container
  - Home Assistant Core
  - tipos de instalación desconocidos
- Cuatro pruebas nuevas.
- Conserva las tres pruebas del Sprint 2.8.1.

## Aplicación

Descomprime el ZIP en la raíz del repositorio y reemplaza los archivos.

Después ejecuta:

```bash
python -m pytest
```

## Registro de la regla

La clase queda definida en:

```text
custom_components/ha_inspector/engine/rules/system.py
```

Si el registro de reglas de tu rama usa una lista explícita, añade
`SupervisorAvailabilityRule()` inmediatamente después de
`SystemInformationRule()`.

Si el catálogo usa `RULE_DESCRIPTORS`, añade:

```python
"SUPERVISOR_AVAILABILITY": RuleDescriptor(
    rule_id="system.supervisor_availability",
    category="system",
    title="Supervisor availability",
    description=(
        "Checks that Supervisor is detectable on installations "
        "that normally include it."
    ),
    weight=10,
    tags=("system", "supervisor", "availability"),
),
```

## Commit sugerido

```bash
git checkout -b sprint-2.8.2-supervisor-availability
git add .
git commit -m "Add Supervisor availability diagnostic"
git push -u origin sprint-2.8.2-supervisor-availability
```
