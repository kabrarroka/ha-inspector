# HA Inspector — Sprint 2.9.2-B4 Fix 3

Corrige el último contrato pendiente detectado por la suite histórica.

Los fallos de collectors y reglas se publican en:

```python
result.metadata["execution_errors"]
```

Formato:

```python
{
    "type": "collector" | "rule",
    "id": "<collector_id o rule_id>",
    "error": "<nombre de la excepción>",
    "message": "<mensaje de la excepción>",
}
```

Se elimina el nombre incorrecto `component_errors`.

## Instalación

Sobrescribe únicamente:

```text
custom_components/ha_inspector/engine/inspector.py
```

## Verificación

```powershell
python -m pytest -q
```

Resultado esperado:

```text
111 passed
1 warning
```
