# HA Inspector — Sprint 2.11.2

## Objetivo

Añadir el adaptador que traduce datos procedentes de un futuro servicio de
Home Assistant a la API interna introducida en el Sprint 2.11.1.

Este sprint sigue sin registrar un servicio real en Home Assistant. El adaptador
es una capa pura y comprobable de forma independiente.

## Arquitectura

```text
Home Assistant service call (Sprint 2.11.3)
                    ↓
       InspectionServiceAdapter
                    ↓
           InspectionRequest
                    ↓
           InspectionService
                    ↓
             RuleEngine
```

## Archivo nuevo

```text
custom_components/ha_inspector/service_adapter.py
```

## InspectionServiceAdapter

Construcción:

```python
adapter = InspectionServiceAdapter(
    service=inspection_service,
)
```

Conversión de datos:

```python
request = adapter.build_request(
    {
        "profile": "quick",
        "strict": True,
    }
)
```

Ejecución:

```python
response = await adapter.async_handle(
    context,
    {
        "categories": ["system"],
        "exclude_tags": ["experimental"],
    },
)
```

## Campos admitidos

```text
profile
rule_ids
categories
tags
exclude_rule_ids
exclude_categories
exclude_tags
strict
```

Los campos desconocidos son rechazados expresamente.

Las selecciones admiten tanto una cadena:

```python
{"rule_ids": "system.core"}
```

como una colección:

```python
{"rule_ids": ["system.core", "system.network"]}
```

## Serialización del resultado

El adaptador admite:

1. resultados que ya sean mappings;
2. objetos que implementen `as_dict()`.

Siempre devuelve una copia independiente preparada para utilizarse como
respuesta de servicio.

## Responsabilidades

El adaptador:

- valida la forma de los datos externos;
- normaliza cadenas y colecciones;
- construye `InspectionRequest`;
- conserva los errores de dominio;
- delega la ejecución en `InspectionService`;
- serializa el resultado.

No:

- registra servicios de Home Assistant;
- accede a `hass`;
- conoce el registro de reglas;
- contiene lógica de selección;
- ejecuta reglas directamente.

## Pruebas añadidas

```text
tests/test_service_adapter.py
```

Cobertura:

1. solicitud vacía;
2. perfil;
3. selección directa;
4. campos desconocidos;
5. validación de `strict`;
6. colecciones inválidas;
7. incompatibilidad perfil/selección;
8. inmutabilidad;
9. delegación;
10. resultado mediante `as_dict`;
11. aislamiento del mapping;
12. `as_dict` inválido;
13. resultado no serializable.

## Estado anterior validado

```text
172 passed
1 warning
```

## Resultado esperado

```text
185 passed
1 warning
```

## Verificación

```powershell
python -m pytest -q
```

## Commit sugerido

```powershell
git add .
git commit -m "Sprint 2.11.2: add inspection service adapter"
git push
```
