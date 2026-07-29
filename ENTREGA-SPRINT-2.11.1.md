# HA Inspector — Sprint 2.11.1

## Objetivo

Introducir una API interna de servicio para convertir solicitudes de inspección
en planes y ejecutarlos mediante `RuleEngine`.

Este sprint no registra todavía un servicio en Home Assistant. Crea primero la
capa de aplicación independiente que utilizará ese adaptador en el siguiente
paso.

## Arquitectura

```text
Home Assistant adapter (futuro)
             ↓
InspectionRequest
             ↓
InspectionService
       ┌─────┴─────┐
       ↓           ↓
 RuleProfiles   RuleSelector
       └─────┬─────┘
             ↓
 RuleExecutionPlan
             ↓
       RuleEngine
```

## InspectionRequest

Solicitud normalizada e inmutable:

```python
request = InspectionRequest(
    categories={"system"},
    tags={"version"},
    exclude_tags={"experimental"},
)
```

También admite perfiles:

```python
request = InspectionRequest(profile="quick")
```

Campos:

```text
profile
rule_ids
categories
tags
exclude_rule_ids
exclude_categories
exclude_tags
strict
```

### Contrato de exclusividad

Un perfil encapsula una selección completa, por lo que no se permite combinar:

```python
InspectionRequest(
    profile="quick",
    categories={"system"},
)
```

Esto produce `InspectionRequestError`.

## InspectionService

Construcción:

```python
service = InspectionService(
    engine=engine,
    selector=selector,
    profiles=profiles,
)
```

Creación del plan:

```python
plan = service.build_plan(request)
```

Ejecución:

```python
result = await service.run(
    context,
    request,
)
```

Sin solicitud explícita:

```python
result = await service.run(context)
```

ejecuta todas las reglas.

## Responsabilidades

`InspectionService`:

- resuelve perfiles;
- construye planes mediante `RuleSelector`;
- transmite `strict`;
- delega la ejecución en `RuleEngine.run_plan`;
- no contiene lógica de coincidencia;
- no conoce Home Assistant;
- no modifica resultados del motor.

## Archivos

Añade:

```text
custom_components/ha_inspector/engine/inspection_service.py
tests/test_inspection_service.py
```

No sobrescribe ningún archivo existente.

## Pruebas añadidas

1. solicitud predeterminada;
2. normalización;
3. perfil vacío;
4. exclusividad entre perfil y criterios;
5. inmutabilidad;
6. selección directa;
7. selección por perfil;
8. ausencia del registro de perfiles;
9. transmisión del modo estricto;
10. delegación al motor;
11. ejecución completa predeterminada;
12. exportación segura.

Suite validada antes de la entrega:

```text
160 passed
1 warning
```

Resultado esperado:

```text
172 passed
1 warning
```

## Verificación

```powershell
python -m pytest -q
```

## Commit sugerido

```powershell
git add .
git commit -m "Sprint 2.11.1: add inspection service API"
git push
```
