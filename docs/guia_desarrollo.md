# Guía de Desarrollo

Guía práctica para implementar cambios en `media-tools` sin degradar la arquitectura ni la mantenibilidad.

## 1. Principio base

Sigue siempre esta dirección de dependencias:

```text
main.py -> ui/ -> services/ -> data/ -> models/
```

`core/` contiene infraestructura compartida y puede ser usada por `main.py`, `data/` o `ui/` cuando sea necesario.

## 2. Ubicación de responsabilidades

### `main.py`

- wiring,
- defaults de configuración,
- creación de servicios,
- callbacks de menú.

### `ui/`

- prompts con `questionary`,
- renderizado con `rich`,
- flujos interactivos.

### `services/`

- reglas de negocio,
- agregación de resultados,
- coordinación entre repositorios y modelos,
- sin impresiones ni input directo.

### `data/`

- ejecución de binarios,
- acceso a filesystem,
- parseo técnico de salidas externas.

### `models/`

- `dataclasses`,
- enums,
- DTOs de entrada y salida.

## 3. Ejemplo correcto de separación

Servicio:

```python
class MediaService:
    def build_clean_plans(self, selection: BrowseResult, keep_languages: list[str]) -> list[CleanPlan]:
        ...
```

Workflow UI:

```python
def run_clean_workflow(service: MediaService, config: ConfigManager) -> None:
    selected = browse_media(config)
    summary = service.audit(selected)
    plans = service.build_clean_plans_from_media_files(summary.report.detailed_files, keep_languages)
    ...
```

## 4. Ejemplo incorrecto

No hacer esto:

```python
class MediaService:
    def run(self) -> None:
        answer = questionary.confirm("¿Continuar?").ask()
        show_warning("Cancelado")
```

Motivo: rompe la separación de capas y dificulta los tests.

## 5. Configuración

`media-tools` debe reutilizar la instancia `self.config` que crea `CLIBaseApp`.

Correcto:

```python
self.config.default_config = {
    "media_root": str(Path.cwd()),
    "keep_languages": ["spa", "eng", "es", "en"],
}
```

Incorrecto:

```python
config = ConfigManager(app_name="media-tools")
```

## 6. Flujo recomendado para implementar una funcionalidad

1. ajustar o crear modelos,
2. actualizar repositorio o adaptador externo,
3. implementar reglas en `services/`,
4. conectar UI o flujo interactivo,
5. enlazarlo en `main.py`,
6. documentar y testear.

## 7. Tests

Cobertura mínima recomendada por feature:

- tests de servicio puro,
- tests de repositorio/adaptador externo,
- tests del flujo interactivo o renderer afectado,
- verificación de arquitectura si el cambio toca límites de capas.

Ejecutar:

```bash
set PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
python -m pytest -q
```

## 8. Checklist antes de cerrar un cambio

- type hints en firmas públicas,
- docstrings en clases y funciones importantes,
- nada de UI dentro de `services/`,
- nada de lógica de negocio en `main.py`,
- documentación actualizada,
- tests verdes.

## 9. Documentos de referencia obligatorios

- [`README.md`](../README.md)
- [`arquitectura.md`](arquitectura.md)
- [`dev_rules.md`](dev_rules.md)
- [`manual.md`](manual.md)
