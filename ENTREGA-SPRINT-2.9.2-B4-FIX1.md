# HA Inspector — Corrección Sprint 2.9.2-B4 Fix 1

Corrige las dos regresiones detectadas por la suite existente:

1. restaura `metadata["rules_executed"]`;
2. vuelve a aislar excepciones de collectors para que la inspección continúe.

También conserva comportamientos relacionados del contrato anterior:

- ordena hallazgos por gravedad descendente y después por `finding_id`;
- registra errores de collectors y reglas en `metadata["component_errors"]`;
- cuenta todos los collectors intentados en `collectors_executed`;
- usa las métricas reales de `ExecutionContext` para `rules_executed`.

## Instalación

Sobrescribe únicamente:

```text
custom_components/ha_inspector/engine/inspector.py
```

No modifiques ningún otro archivo de B1–B4.

## Verificación

```powershell
python -m pytest -q
```

Resultado esperado:

```text
111 passed
1 warning
```

## Commit sugerido

```powershell
git add custom_components/ha_inspector/engine/inspector.py
git commit -m "Fix B4 inspector compatibility metadata and collector isolation"
git push
```
