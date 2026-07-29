# HA Inspector — Sprint 2.9.2-B1

## Objetivo

Introducir un motor de ejecución de reglas completamente desacoplado del
`Inspector` actual.

Esta entrega no modifica:

- `Inspector`;
- `InspectionResult`;
- collectors;
- descubrimiento de reglas;
- salida pública de diagnósticos.

## Nuevo componente

```text
custom_components/ha_inspector/engine/rule_engine.py
```

`RuleEngine`:

- recibe una secuencia de reglas;
- conserva el orden de declaración;
- ejecuta cada `check(context)`;
- mide su duración con reloj monotónico;
- devuelve un `RuleExecutionResult` por regla;
- captura excepciones para que una regla no detenga las siguientes;
- expone las reglas mediante una tupla inmutable.

## Pruebas añadidas

```text
tests/test_rule_engine.py
```

Cubren:

- orden de ejecución;
- Findings producidos;
- tiempo por regla;
- aislamiento de excepciones;
- continuación tras un fallo;
- lista de reglas inmutable;
- motor vacío.

## Instalación manual

Desde el contenido descomprimido, copia:

```text
custom_components/ha_inspector/engine/rule_engine.py
tests/test_rule_engine.py
```

a las mismas rutas del repositorio.

Después ejecuta:

```powershell
python -m pytest -q
```

La suite anterior tenía 94 pruebas. Esta entrega añade cinco, por lo que el
resultado esperado es:

```text
99 passed
```

Puede continuar apareciendo la advertencia externa de Home Assistant/aiohttp.

## Commit sugerido

```powershell
git add .
git commit -m "Sprint 2.9.2-B1: introduce independent rule engine"
git push
```

## Próximo paso

La Entrega B2 añadirá `ExecutionContext` sin conectar todavía el motor con
`Inspector`.
