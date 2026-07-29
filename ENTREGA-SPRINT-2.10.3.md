# HA Inspector — Sprint 2.10.3

## Objetivo

Añadir perfiles reutilizables de selección de reglas sin duplicar la lógica de
`RuleSelector`.

## Arquitectura

```text
RuleProfile
      ↓
RuleSelection
      ↓
RuleProfiles.select()
      ↓
RuleSelector
      ↓
RuleExecutionPlan
```

## RuleProfile

Objeto inmutable con:

- `name`;
- `title` opcional;
- `description` opcional;
- `selection`.

Ejemplo:

```python
quick = RuleProfile(
    name="quick",
    title="Quick",
    description="Fast system checks.",
    selection=RuleSelection(
        include_categories={"system"},
        exclude_tags={"experimental"},
    ),
)
```

## RuleProfiles

Registro inmutable y determinista:

```python
profiles = RuleProfiles(
    [
        quick,
        network,
        full,
    ]
)
```

API:

```python
profiles.names
profiles.list_profiles()
profiles.get("quick")
profiles.select("quick", selector)
profiles.as_dicts()
```

## Semántica

- Los nombres se normalizan eliminando espacios exteriores.
- Los nombres vacíos se rechazan.
- Los nombres duplicados producen `RuleProfileError`.
- El orden público es determinista por nombre.
- Los perfiles no ejecutan reglas.
- La selección se delega completamente a `RuleSelector`.
- `strict=True` conserva la validación estricta existente.
- `strict=False` permite perfiles tolerantes.
- El registro vacío es válido.
- Las exportaciones son copias JSON-friendly.

## Archivos

Añade:

```text
custom_components/ha_inspector/engine/rule_profile.py
custom_components/ha_inspector/engine/rule_profiles.py
tests/test_rule_profiles.py
```

No sobrescribe ningún archivo existente.

## Pruebas añadidas

1. normalización;
2. validación de campos;
3. inmutabilidad;
4. orden determinista;
5. pertenencia y recuperación;
6. perfil desconocido;
7. duplicados;
8. registro vacío;
9. generación de planes;
10. modo estricto y tolerante;
11. exportación segura.

La suite validada contiene 149 pruebas.

Resultado esperado:

```text
160 passed
1 warning
```

## Verificación

```powershell
python -m pytest -q
```

## Commit sugerido

```powershell
git add .
git commit -m "Sprint 2.10.3: add reusable rule profiles"
git push
```
