# HA Inspector — Sprint 2.10.2

## Objetivo

Añadir una API de selección de alto nivel que traduzca criterios de usuario en
un `RuleExecutionPlan` ejecutable.

## Arquitectura

```text
Petición de usuario
        ↓
RuleSelection
        ↓
RuleSelector
  ├── RuleRegistry       validación
  ├── RuleFilter         coincidencias
  └── RuleExecutionPlan  resultado
```

## API principal

```python
selector = RuleSelector(rules)

plan = selector.select(
    include_categories={"system"},
    include_tags={"version"},
    exclude_tags={"experimental"},
)
```

También permite seleccionar reglas concretas:

```python
plan = selector.select(
    include_rule_ids={
        "system.core_version",
        "system.supervisor_version",
    }
)
```

## Semántica

- Sin criterios se seleccionan todas las reglas.
- Las dimensiones de inclusión se combinan por intersección.
- Dentro de una misma dimensión basta con coincidir con uno de sus valores.
- Las exclusiones se aplican después y siempre tienen prioridad.
- Una inclusión explícitamente vacía selecciona cero reglas.
- El orden del plan conserva el orden de las reglas suministradas.
- El resultado es un `RuleExecutionPlan` inmutable.

Ejemplo:

```python
include_categories={"system"}
include_tags={"version", "network"}
exclude_tags={"experimental"}
```

Selecciona reglas de categoría `system` que tengan `version` o `network`, salvo
las etiquetadas como `experimental`.

## Validación

Por defecto, el modo es estricto:

```python
selector.select(include_tags={"unknown"})
```

produce `RuleSelectionError`.

Esto evita que una errata en una futura llamada desde Home Assistant genere una
inspección vacía sin explicación.

Para consumidores que necesiten tolerancia:

```python
selector.select(
    include_tags={"unknown"},
    strict=False,
)
```

## Objetos nuevos

### RuleSelection

Petición normalizada e inmutable con:

- `include_rule_ids`;
- `include_categories`;
- `include_tags`;
- `exclude_rule_ids`;
- `exclude_categories`;
- `exclude_tags`.

### RuleSelector

Expone:

```python
selector.registry
selector.select(...)
selector.as_filter(selection)
```

## Archivos

Añade:

```text
custom_components/ha_inspector/engine/rule_selector.py
tests/test_rule_selector.py
```

No sobrescribe ningún archivo existente.

## Pruebas añadidas

1. acceso al registro;
2. selección completa;
3. inclusión por identificadores;
4. intersección entre dimensiones;
5. unión dentro de una dimensión;
6. prioridad de exclusiones;
7. exclusión por categoría y etiqueta;
8. inclusión vacía;
9. validación estricta;
10. modo no estricto;
11. normalización e inmutabilidad.

La suite validada contiene 138 pruebas.

Resultado esperado:

```text
149 passed
1 warning
```

## Verificación

```powershell
python -m pytest -q
```

## Commit sugerido

```powershell
git add .
git commit -m "Sprint 2.10.2: add rule selection API"
git push
```
