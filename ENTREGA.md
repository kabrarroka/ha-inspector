# HA Inspector — Sprint 2.5.1

Primera infraestructura de calidad para el proyecto.

## Contenido

- `tests/test_inspection_result.py`
- `tests/test_engine_registry.py`
- `tests/test_rule_descriptor.py`
- `pytest.ini`
- `requirements-dev.txt`
- `.github/workflows/tests.yml`
- `.gitignore`

## Aplicación

Copiar todos los archivos en la raíz del repositorio `ha-inspector`, conservando las rutas.

## Prueba local

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

## Rama sugerida

```bash
git switch -c sprint-2.5.1-tests-ci
git add .
git commit -m "Add pytest and GitHub Actions test infrastructure"
git push -u origin sprint-2.5.1-tests-ci
```
