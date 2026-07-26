# HA Inspector — Sprint 2.8.6

## Objetivo

Añadir `FrontendVersionRule` y soporte específico para versiones del
Frontend.

## Formato

El Frontend utiliza versiones basadas en fecha y revisión:

```text
20260624.5
20260723.0
```

El parser comprueba:

- ocho dígitos de fecha `AAAAMMDD`;
- un punto;
- una revisión numérica;
- que la fecha exista realmente.

No intenta deducir beta, RC o desarrollo. Esa condición pertenece a los
metadatos de la publicación y no queda codificada de forma fiable en la
cadena de versión.

## Archivos

```text
custom_components/ha_inspector/engine/utils/versions.py
custom_components/ha_inspector/engine/rules/frontend_version.py
tests/test_version_utils.py
tests/test_frontend_version_rule.py
```

Los dos archivos existentes sustituyen sus versiones anteriores conservando
las pruebas y funciones previas.

## Catálogo

Añade a `RULE_DESCRIPTORS`:

```python
"FRONTEND_VERSION": RuleDescriptor(
    rule_id="system.frontend_version",
    category="system",
    title="Home Assistant Frontend version",
    description=(
        "Checks whether the reported Home Assistant Frontend version "
        "uses a valid date-based format."
    ),
    weight=5,
    tags=("system", "version", "frontend"),
),
```

No instancies la regla. `discovery.py` la encontrará automáticamente.

## Pruebas

```powershell
python -m pytest -q
```

Prueba aislada:

```powershell
python -m pytest -q tests/test_version_utils.py tests/test_frontend_version_rule.py
```

## Commit sugerido

```powershell
git add .
git commit -m "Sprint 2.8.6: add Frontend version rule"
git push
```
