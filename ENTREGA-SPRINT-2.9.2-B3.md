# HA Inspector — Sprint 2.9.2-B3

## Objetivo

Conectar `ExecutionContext` con `RuleEngine` y validar ambos componentes como
un motor completo, todavía desacoplado de `Inspector`.

## Archivo actualizado

```text
custom_components/ha_inspector/engine/rule_engine.py
```

Cambios principales:

- cada llamada a `run()` crea un `ExecutionContext` nuevo;
- `ExecutionContext` mide la duración individual de las reglas;
- registra reglas ejecutadas, correctas y fallidas;
- finaliza automáticamente al terminar todas las reglas;
- el motor expone el contexto de su ejecución más reciente;
- se mantiene el aislamiento de excepciones;
- se conserva la API de retorno de B1:
  `tuple[RuleExecutionResult, ...]`.

## Pruebas actualizadas

```text
tests/test_rule_engine.py
```

Las cinco pruebas de B1 se adaptan al nuevo cronómetro centralizado y se añaden
dos pruebas:

- exposición del contexto finalizado y sus métricas;
- creación de un contexto independiente en cada ejecución.

## Archivos que deben copiarse

Esta entrega reemplaza archivos existentes. Copia y sobrescribe:

```text
custom_components/ha_inspector/engine/rule_engine.py
tests/test_rule_engine.py
```

No cambies ni elimines:

```text
custom_components/ha_inspector/engine/execution_context.py
tests/test_execution_context.py
```

## Verificación

Ejecuta:

```powershell
python -m pytest -q
```

La suite tenía 106 pruebas. B3 añade dos pruebas nuevas:

```text
108 passed
```

Puede continuar apareciendo el warning externo habitual de Home Assistant.

## Commit sugerido

```powershell
git add .
git commit -m "Sprint 2.9.2-B3: integrate execution context into rule engine"
git push
```

## Próximo paso

La Entrega B4 sustituirá el bucle interno de reglas de `Inspector` por
`RuleEngine`, conservará exactamente la salida pública y añadirá pruebas de
compatibilidad para evitar regresiones.
