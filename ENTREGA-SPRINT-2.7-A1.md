# HA Inspector — Sprint 2.7 A1

Primera entrega del sensor de diagnóstico.

## Incluye

- Almacenamiento en memoria del último resultado.
- Nueva plataforma `sensor`.
- Entidad `sensor.ha_inspector_status`.
- Estados: `not_run`, `ok`, `info`, `warning`, `error` y `critical`.
- Actualización inmediata al ejecutar `ha_inspector.run`.
- Atributos con puntuación, hallazgos, comprobaciones, duración y categorías.
- Tests del cálculo de estado.

## Aplicación

Descomprime este ZIP en la raíz del repositorio, estando en la rama:

```bash
git checkout sprint-2.7-diagnostic-sensor
```

Permite reemplazar los archivos existentes y ejecuta:

```bash
python -m pytest
git add .
git commit -m "Add diagnostic status sensor"
git push
```

Después copia la integración actualizada a Home Assistant y reinicia.

## Prueba en Home Assistant

Ejecuta la acción:

```yaml
action: ha_inspector.run
response_variable: informe
```

Después comprueba la entidad:

```text
sensor.ha_inspector_status
```
