# HA Inspector — Sprint 2.10.1

## Objetivo

Introducir un catálogo de reglas que permita consultar sus metadatos sin
ejecutarlas.

## Separación de responsabilidades

El proyecto ya dispone de `EngineRegistry`, cuya responsabilidad es descubrir
clases e instanciar collectors y reglas.

Este sprint añade `RuleRegistry`, cuya responsabilidad es diferente:

```text
EngineRegistry
    └── descubre e instancia reglas
                 ↓
RuleRegistry
    └── cataloga metadatos inmutables
```

No se modifica el registro de descubrimiento existente.

## API

```python
registry = RuleRegistry(rules)

registry.list_rules()
registry.get_rule("system.core_version")
registry.categories()
registry.tags()
registry.as_dicts()
```

También admite filtros combinables:

```python
registry.list_rules(category="system")
registry.list_rules(tag="version")
registry.list_rules(category="system", tag="version")
```

## RuleRegistryEntry

Cada regla se convierte, sin ejecutarla, en una instantánea inmutable con:

- `rule_id`;
- `title`;
- `category`;
- `severity`;
- `tags`;
- `weight`;
- `recommendation`.

`as_dict()` devuelve una copia JSON-friendly, adecuada para futuros servicios,
diagnósticos o interfaz.

## Contratos

- El orden público es determinista por `rule_id`.
- Las reglas nunca se ejecutan para construir el catálogo.
- Los identificadores duplicados producen `RuleRegistryError`.
- Un identificador desconocido produce `KeyError`.
- Un registro vacío es válido.
- Las colecciones exportadas no pueden mutar el registro interno.
- Los filtros por categoría y etiqueta se combinan mediante intersección.

## Archivos

Añade:

```text
custom_components/ha_inspector/engine/rule_registry.py
tests/test_rule_registry.py
```

No sobrescribe ningún archivo existente.

## Pruebas añadidas

1. construcción sin ejecutar reglas;
2. orden determinista;
3. instantánea completa;
4. identificador desconocido;
5. pertenencia;
6. filtros;
7. categorías y etiquetas;
8. copias JSON seguras;
9. duplicados;
10. registro vacío.

La suite validada contiene 128 pruebas.

Resultado esperado:

```text
138 passed
1 warning
```

## Verificación

```powershell
python -m pytest -q
```

## Commit sugerido

```powershell
git add .
git commit -m "Sprint 2.10.1: add rule metadata registry"
git push
```
