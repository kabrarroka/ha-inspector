# HA Inspector — Sprint 2.9.2-B4 Fix 2

Esta corrección ajusta B4 al contrato confirmado por las pruebas históricas.

## Semántica restaurada

- `rules_discovered`: número total de reglas configuradas.
- `ExecutionContext.rules_executed`: número total de reglas intentadas por el motor.
- `InspectionResult.metadata["rules_executed"]`: reglas finalizadas correctamente.
- `InspectionResult.checks_executed`: reglas finalizadas correctamente.
- Una regla fallida se registra en `component_errors`, pero no se añade a
  `InspectionResult` ni altera categorías, puntuación o contador de checks.
- `collectors_executed` cuenta collectors finalizados correctamente.
- Los fallos de collectors y reglas no detienen la inspección.

## Archivos

Sobrescribe:

```text
custom_components/ha_inspector/engine/inspector.py
tests/test_inspector_rule_engine.py
```

## Verificación

```powershell
python -m pytest -q
```

Resultado esperado:

```text
111 passed
1 warning
```
