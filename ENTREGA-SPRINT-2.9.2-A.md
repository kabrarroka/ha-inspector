# HA Inspector — Sprint 2.9.2, Entrega A

## Objetivo

Introducir los modelos de resultado que utilizará el futuro `RuleEngine`,
sin modificar todavía el flujo actual de ejecución.

## Archivos

```text
custom_components/ha_inspector/engine/result.py
tests/test_inspection_result.py
```

## `RuleExecutionResult`

Representa una única ejecución:

```python
RuleExecutionResult(
    rule_id="CORE_VERSION",
    duration_ms=1.35,
    findings=(),
    success=True,
    error=None,
)
```

Incluye:

- identificador de la regla;
- duración en milisegundos;
- Findings producidos;
- estado correcto o fallido;
- mensaje de error seguro;
- serialización con `as_dict()`.

## `InspectionResult`

Representa la ejecución completa:

```python
InspectionResult(
    findings=(),
    executions=(),
    duration_ms=8.25,
    skipped_rules=0,
)
```

Calcula automáticamente:

- `executed_rules`;
- `successful_rules`;
- `failed_rules`;
- `skipped_rules`;
- `total_rules`;
- `finding_count`;
- `success`.

## Decisiones de diseño

Los modelos son:

- inmutables mediante `frozen=True`;
- compactos mediante `slots=True`;
- serializables;
- independientes de Home Assistant;
- compatibles con el `Finding` actual.

Las colecciones son tuplas para impedir que el resultado cambie
accidentalmente después de terminar una inspección.

## Instalación

Copia el contenido del ZIP sobre la raíz del repositorio.

No hay que modificar `catalog.py`: estos modelos no son reglas.

## Pruebas

```powershell
python -m pytest -q
```

Prueba aislada:

```powershell
python -m pytest -q tests/test_inspection_result.py
```

## Commit sugerido

```powershell
git add .
git commit -m "Sprint 2.9.2-A: add inspection result models"
git push
```

## Siguiente entrega

La Entrega B añadirá `RuleEngine`, que construirá estos resultados, medirá
cada ejecución y capturará errores sin detener el resto de reglas.
