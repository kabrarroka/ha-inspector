# Integración mínima en `__init__.py`

La copia pública del repositorio todavía contiene el servicio antiguo
`ha_inspector.run`, mientras que la copia local del proyecto está varios
sprints por delante. Por ese motivo esta entrega no reemplaza automáticamente
`__init__.py`.

## 1. Importaciones

Añadir:

```python
from .services import (
    async_register_services,
    async_unregister_services,
)
```

## 2. Después de construir `InspectionServiceAdapter`

En el punto de configuración global donde ya estén disponibles
`InspectionService` y `InspectionServiceAdapter`:

```python
inspection_service = InspectionService(
    registry=rule_registry,
    selector=rule_selector,
    profiles=rule_profiles,
    engine=rule_engine,
)

service_adapter = InspectionServiceAdapter(
    service=inspection_service,
)

async_register_services(
    hass,
    service_adapter,
)
```

Usar los argumentos reales que tenga el constructor local de
`InspectionService`; el bloque anterior muestra el flujo, no sustituye la API
ya validada del Sprint 2.11.1.

## 3. Descarga final de la integración

En el punto donde se descargue globalmente HA Inspector:

```python
async_unregister_services(hass)
```

El servicio debe registrarse una sola vez a nivel de integración. No debe
registrarse una vez por cada config entry.

## Servicio anterior

Cuando `ha_inspector.run_inspection` esté validado, retirar el registro antiguo
de `ha_inspector.run` para evitar dos caminos de ejecución distintos.
No eliminarlo en esta entrega si todavía se utiliza para pruebas manuales.
