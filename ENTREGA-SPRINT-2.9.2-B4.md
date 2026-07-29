# HA Inspector — Sprint 2.9.2-B4

## Objetivo

Integrar `RuleEngine` en `Inspector` y retirar el bucle directo de ejecución de
reglas, manteniendo la API y el resultado público existentes.

## Archivo actualizado

```text
custom_components/ha_inspector/engine/inspector.py
```

El flujo pasa a ser:

```text
Collectors
    ↓
InspectionContext
    ↓
RuleEngine
    ↓
RuleExecutionResult
    ↓
InspectionResult
```

`Inspector` conserva sus responsabilidades de orquestación:

- crear `InspectionContext`;
- ejecutar collectors;
- solicitar la ejecución de reglas al motor;
- trasladar los hallazgos a `InspectionResult`;
- construir los metadatos públicos;
- filtrar los datos sensibles de diagnostics;
- finalizar el resultado.

`Inspector` ya no:

- llama directamente a `rule.check()`;
- mide o controla la ejecución de reglas;
- gestiona excepciones individuales de reglas.

## Compatibilidad pública

Se conservan:

- `Inspector.run(hass, diagnostics=False)`;
- `InspectionResult`;
- `checks_executed`;
- hallazgos y puntuación;
- categorías;
- `collectors_executed`;
- `rules_discovered`;
- `diagnostics_included`;
- catálogo de reglas en diagnostics;
- contexto seguro de diagnostics.

Una regla que lance una excepción queda aislada por `RuleEngine`; las reglas
posteriores continúan ejecutándose. La regla fallida cuenta como comprobación
ejecutada y no aporta hallazgos ni penalización.

## Pruebas añadidas

```text
tests/test_inspector_rule_engine.py
```

Incluye tres pruebas de integración:

1. conservación del resultado público;
2. conservación del catálogo y contexto de diagnostics;
3. aislamiento de fallos y continuación de reglas.

## Instalación

Sobrescribe:

```text
custom_components/ha_inspector/engine/inspector.py
```

Añade:

```text
tests/test_inspector_rule_engine.py
```

Mantén sin cambios los archivos B1, B2 y B3 instalados anteriormente.

## Verificación

Ejecuta:

```powershell
python -m pytest -q
```

La suite tenía 108 pruebas. Esta entrega añade tres:

```text
111 passed
```

Puede aparecer el warning habitual externo de Home Assistant.

## Commit sugerido

```powershell
git add .
git commit -m "Sprint 2.9.2-B4: integrate rule engine into inspector"
git push
```

## Resultado arquitectónico

Con B4 queda completada la fase 2.9.2-B:

```text
Inspector           orquestación
RuleEngine          ejecución de reglas
ExecutionContext    estado y métricas internas
RuleExecutionResult resultado individual
InspectionResult    resultado público
```
