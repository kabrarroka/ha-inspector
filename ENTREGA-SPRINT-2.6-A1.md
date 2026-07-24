# HA Inspector — Sprint 2.6 A1

Primera entrega funcional del Sprint 2.6.

## Incluye

- Detección de nombres amigables duplicados.
- Detección de automatizaciones deshabilitadas en el registro de entidades.
- Ampliación del colector de entidades.
- Cuatro tests unitarios nuevos.
- Conserva las reglas existentes de entidades unavailable y unknown.

## Aplicación

Descomprime el ZIP en la raíz del repositorio y permite reemplazar los archivos existentes.

Después ejecuta:

```bash
python -m pytest
```

## Commit sugerido

```bash
git add .
git commit -m "Add duplicate name and disabled automation rules"
git push -u origin sprint-2.6-rules
```
