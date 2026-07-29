# HA Inspector — Sprint 2.9.3-B

## Objetivo

Separar la selección de reglas de su ejecución mediante un plan inmutable.

## Nueva arquitectura

```text
RuleFilter
    ↓
RuleEngine.build_plan()
    ↓
RuleExecutionPlan
    ↓
RuleEngine.run_plan()
    ↓
RuleExecutionResult
```

## RuleExecutionPlan

El nuevo objeto conserva:

- reglas exactas que se ejecutarán;
- orden de ejecución;
- identificadores ordenados;
- categorías únicas por orden de aparición;
- estado vacío.

El plan copia la secuencia recibida a una tupla, por lo que cambios posteriores
en la lista original no afectan a la ejecución.

## API del motor

Se añade:

```python
plan = engine.build_plan(
    RuleFilter(categories={"system"})
)

results = await engine.run_plan(context, plan)
```

La API histórica permanece intacta:

```python
results = await engine.run(context)

results = await engine.run(
    context,
    rule_filter=RuleFilter(categories={"system"}),
)
```

`run()` ahora construye internamente un plan y delega en `run_plan()`.

También se expone el plan de la última ejecución:

```python
engine.execution_plan
```

## Compatibilidad

Se conserva:

- `RuleEngine.select_rules()`;
- retorno de `run()` como `tuple[RuleExecutionResult, ...]`;
- orden original;
- aislamiento de errores;
- `ExecutionContext`;
- comportamiento con cero reglas;
- contratos de `Inspector` e `InspectionResult`.

## Archivos

Añade:

```text
custom_components/ha_inspector/engine/execution_plan.py
tests/test_execution_plan.py
```

Sobrescribe:

```text
custom_components/ha_inspector/engine/rule_engine.py
```

## Pruebas añadidas

1. congelación de la secuencia fuente;
2. metadatos ordenados;
3. plan vacío;
4. plan sin filtro;
5. plan filtrado;
6. compatibilidad de `select_rules()`;
7. exposición del plan ejecutado;
8. ejecución directa de un plan preconstruido.

La suite validada contiene 120 pruebas.

Resultado esperado:

```text
128 passed
1 warning
```

## Verificación

```powershell
python -m pytest -q
```

## Commit sugerido

```powershell
git add .
git commit -m "Sprint 2.9.3-B: add rule execution plans"
git push
```
