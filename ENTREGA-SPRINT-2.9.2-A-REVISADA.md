# HA Inspector — Sprint 2.9.2-A revisada

## Motivo de la revisión

La primera entrega sustituyó accidentalmente el `InspectionResult` existente.
El `Inspector` actual depende de su método `record_rule()`, por lo que tres
pruebas quedaron en rojo.

Esta entrega vuelve a partir del archivo real del repositorio y mantiene
íntegra su API.

## Cambios

### Nuevo modelo

Se añade:

```python
RuleExecutionResult
```

Contiene:

- `rule_id`;
- `duration_ms`;
- Findings producidos;
- estado correcto o fallido;
- mensaje de error;
- `finding_count`;
- serialización mediante `as_dict()`.

### Compatibilidad conservada

`InspectionResult` mantiene sin cambios funcionales:

- `record_rule()`;
- `add_many()`;
- `finish()`;
- puntuación;
- categorías;
- metadatos;
- esquema de salida `RESULT_SCHEMA_VERSION = 2`;
- `as_dict()`.

El `Inspector` actual no se modifica.

## Archivos

```text
custom_components/ha_inspector/engine/result.py
tests/test_rule_execution_result.py
```

Al copiar esta entrega, puede eliminarse el archivo de pruebas de la primera
versión fallida:

```text
tests/test_inspection_result.py
```

La entrega incluye un script para hacerlo automáticamente en Windows.

## Instalación en PowerShell

Descomprime el ZIP sobre la raíz del repositorio y ejecuta:

```powershell
.\APLICAR-SPRINT-2.9.2-A-REVISADA.ps1
python -m pytest -q
```

El script:

1. copia el `result.py` revisado;
2. copia las pruebas nuevas;
3. elimina `tests/test_inspection_result.py` si quedó de la entrega anterior.

## Commit sugerido

```powershell
git add .
git commit -m "Sprint 2.9.2-A: add compatible rule execution model"
git push
```

## Siguiente entrega

Sprint 2.9.2-B adaptará `Inspector` para medir tiempos y construir
`RuleExecutionResult`, manteniendo el resultado público actual.
