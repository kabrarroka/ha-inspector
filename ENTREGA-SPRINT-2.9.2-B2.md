# HA Inspector — Sprint 2.9.2-B2

## Objetivo

Añadir `ExecutionContext`, responsable exclusivamente del estado interno de una
ejecución del motor.

Esta entrega no modifica:

- `RuleEngine`;
- `Inspector`;
- `InspectionResult`;
- `InspectionContext`;
- la salida pública de la integración.

## Nuevo componente

```text
custom_components/ha_inspector/engine/execution_context.py
```

El contexto registra:

- número total de reglas;
- inicio y final de la ejecución mediante reloj monotónico;
- regla actualmente activa;
- inicio de la regla activa;
- reglas ejecutadas;
- reglas correctas;
- reglas fallidas;
- progreso normalizado entre `0.0` y `1.0`;
- duración total;
- duración individual de cada regla.

También protege transiciones inválidas:

- ejecutar dos reglas simultáneamente;
- completar sin regla activa;
- finalizar mientras una regla sigue activa;
- finalizar antes de ejecutar todas las reglas;
- iniciar reglas después de finalizar.

## Pruebas añadidas

```text
tests/test_execution_context.py
```

Se añaden siete pruebas para:

- progreso y ejecución correcta;
- conteo de fallos;
- duración total estable;
- ejecución sin reglas;
- transiciones inválidas;
- validación del total;
- finalización prematura.

## Instalación manual

Copia estos archivos a las mismas rutas del repositorio:

```text
custom_components/ha_inspector/engine/execution_context.py
tests/test_execution_context.py
```

Después ejecuta:

```powershell
python -m pytest -q
```

La suite tenía 99 pruebas. Esta entrega añade siete:

```text
106 passed
```

Puede continuar apareciendo el warning externo habitual de Home Assistant.

## Commit sugerido

```powershell
git add .
git commit -m "Sprint 2.9.2-B2: add rule execution context"
git push
```

## Próximo paso

La Entrega B3 conectará `ExecutionContext` con `RuleEngine`. Todavía no
modificará `Inspector`; primero validaremos conjuntamente ambos componentes.
