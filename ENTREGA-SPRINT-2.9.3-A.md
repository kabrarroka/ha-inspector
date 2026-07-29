# HA Inspector — Sprint 2.9.3-A

## Objetivo

Añadir selección de reglas al motor sin modificar el comportamiento existente
cuando no se proporciona ningún filtro.

## Arquitectura

Se incorpora:

```text
RuleFilter
    ↓
RuleEngine.select_rules()
    ↓
RuleEngine.run(..., rule_filter=...)
    ↓
ExecutionContext(total_rules=reglas seleccionadas)
```

## Capacidades

`RuleFilter` permite seleccionar por:

- identificadores de regla;
- categorías;
- predicado interno.

Ejemplo:

```python
rule_filter = RuleFilter(
    rule_ids={"system.alpha", "system.gamma"},
    categories={"system"},
)

executions = await engine.run(
    context,
    rule_filter=rule_filter,
)
```

Cuando se proporcionan varios criterios, todos deben cumplirse. Por tanto, se
combinan mediante intersección.

La selección siempre conserva el orden original de declaración de las reglas.

## Semántica

- `RuleFilter()` selecciona todas las reglas.
- `None` mantiene el comportamiento histórico.
- `RuleFilter(rule_ids=[])` selecciona cero reglas.
- IDs o categorías vacíos o formados solo por espacios producen `ValueError`.
- `ExecutionContext.total_rules` refleja exclusivamente las reglas
  seleccionadas.
- Una ejecución sin reglas seleccionadas termina correctamente con progreso
  `1.0`.

## Compatibilidad

La llamada histórica sigue siendo válida y no cambia:

```python
await engine.run(context)
```

No se modifica:

- `InspectionResult`;
- `Inspector`;
- formato de findings;
- aislamiento de excepciones;
- orden de ejecución;
- métricas existentes.

Esta primera fase expone el filtrado en `RuleEngine`. Una fase posterior podrá
conectarlo a `Inspector`, servicios o interfaz sin mezclar responsabilidades.

## Archivos

Añade:

```text
custom_components/ha_inspector/engine/rule_filter.py
tests/test_rule_filter.py
```

Sobrescribe:

```text
custom_components/ha_inspector/engine/rule_engine.py
```

## Pruebas

Se añaden ocho pruebas:

1. filtro sin criterios;
2. selección por IDs;
3. selección por categoría;
4. intersección de criterios;
5. predicado interno;
6. ejecución parcial y métricas;
7. selección explícitamente vacía;
8. validación de valores vacíos.

La suite anterior tenía 111 pruebas.

Resultado esperado:

```text
119 passed
1 warning
```

## Verificación

```powershell
python -m pytest -q
```

## Commit sugerido

```powershell
git add .
git commit -m "Sprint 2.9.3-A: add rule filtering"
git push
```
