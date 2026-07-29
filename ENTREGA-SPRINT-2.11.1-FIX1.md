# HA Inspector — Sprint 2.11.1 Fix 1

## Problema

Las seis pruebas fallaban al construir `RuleSelector` porque el doble
`FakeRule` devolvía el propio objeto como `metadata`.

`RuleRegistryEntry.from_rule()` utiliza:

```python
rule.metadata.as_dict()
```

El doble no implementaba ese contrato.

## Solución

Se sustituye `FakeRule` por tres subclases reales de `BaseRule`:

- `SystemCoreRule`
- `SystemNetworkRule`
- `VersionFrontendRule`

Así las pruebas utilizan la misma API de metadatos que las reglas reales y que
los sprints anteriores.

## Archivo sustituido

```text
tests/test_inspection_service.py
```

El código de producción de `InspectionService` no necesita cambios.

## Resultado esperado

```text
172 passed
1 warning
```

## Verificación

```powershell
python -m pytest -q
```
