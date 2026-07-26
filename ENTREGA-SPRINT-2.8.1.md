# HA Inspector — Sprint 2.8.1

## Objetivo

Ampliar el inventario del sistema sin crear un segundo modelo de reglas o
metadatos.

## Cambios

- Usa `homeassistant.helpers.system_info.async_get_system_info`.
- Añade el tipo de instalación.
- Obtiene la versión instalada de Supervisor desde su entidad `update`.
- Obtiene la versión instalada de Home Assistant OS desde su entidad `update`.
- Obtiene la versión del paquete `home-assistant-frontend`.
- Conserva los datos anteriores de Python, plataforma, arquitectura y zona horaria.
- Amplía `SystemInformationRule`.
- Añade tres pruebas unitarias.

Los campos de Supervisor y HAOS son opcionales. En Home Assistant Container o
Core se devolverán como `None`, sin producir errores.

## Aplicación

Descomprime este ZIP en la raíz del repositorio y permite reemplazar los
archivos existentes.

Ejecuta:

```bash
python -m pytest
```

## Commit sugerido

```bash
git checkout -b sprint-2.8.1-system-info
git add .
git commit -m "Expand system installation information"
git push -u origin sprint-2.8.1-system-info
```
