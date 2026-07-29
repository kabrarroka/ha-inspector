# HA Inspector — Sprint 2.11.3

## Objetivo

Registrar el primer servicio nativo basado en la nueva arquitectura:

```text
ha_inspector.run_inspection
```

El servicio devuelve respuesta obligatoria y delega todo el trabajo en
`InspectionServiceAdapter`.

## Archivos

```text
custom_components/ha_inspector/services.py
custom_components/ha_inspector/services.yaml
tests/test_services.py
PATCH-INIT-SPRINT-2.11.3.md
```

## Flujo

```text
ServiceCall
    ↓
services.py
    ↓
InspectionServiceAdapter
    ↓
InspectionService
    ↓
RuleEngine
    ↓
ServiceResponse
```

## Ejemplo

```yaml
action: ha_inspector.run_inspection
data:
  profile: quick
response_variable: inspection
```

Selección directa:

```yaml
action: ha_inspector.run_inspection
data:
  categories:
    - system
  exclude_tags:
    - experimental
  strict: true
response_variable: inspection
```

## Comportamiento

- Registro idempotente.
- Respuesta obligatoria mediante `SupportsResponse.ONLY`.
- Esquema Voluptuous con campos conocidos.
- Errores de solicitud convertidos en `ServiceValidationError`.
- Errores inesperados convertidos en `HomeAssistantError`.
- Desregistro idempotente.
- El manejador no contiene lógica de selección ni ejecución.

## Pruebas añadidas

Se añaden 13 casos lógicos; la parametrización de errores produce varios casos
pytest adicionales.

## Estado anterior

```text
185 passed
1 warning
```

## Resultado esperado

Dependiendo del conteo de parametrizaciones:

```text
198 passed
1 warning
```

## Verificación

```powershell
python -m pytest -q
```

## Nota sobre `__init__.py`

La entrega incluye un parche guiado, no un reemplazo, porque el repositorio
público aún contiene una versión antigua y sobrescribir el archivo local
pondría en riesgo los sprints ya validados.
