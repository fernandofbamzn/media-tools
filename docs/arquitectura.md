# Arquitectura de media-tools

Documento de referencia técnica del proyecto.

## Vista general

```text
main.py -> ui/ -> services/ -> data/ -> models/
              \-> core/ (config, excepciones, utilidades)
```

## Objetivo de la arquitectura

- separar la interacción de usuario de la lógica de negocio,
- aislar llamadas a binarios externos,
- hacer los servicios fáciles de probar,
- mantener wiring y configuración en un solo sitio.

## Estructura

```text
media-tools/
├── main.py
├── core/
├── data/
├── models/
├── services/
├── ui/
├── docs/
└── tests/
```

## Responsabilidades por capa

### `main.py`

- inicializa `MediaToolsApp`,
- define `self.config.default_config`,
- crea servicios y conecta callbacks,
- no implementa reglas de negocio largas.

### `ui/`

- `components.py`: renderers específicos,
- `clean_menu.py`: selección interactiva de pistas,
- `workflows.py`: flujo integrado de navegación, auditoría, planificación y limpieza.

### `services/`

- `audit_service.py`: estadísticas agregadas,
- `clean_service.py`: reglas para conservar o eliminar pistas,
- `media_service.py`: orquestación pura sobre repositorio y servicios.

### `data/`

- `repository.py`: llamadas a `mkvmerge`, parseo JSON y remux.

### `models/`

- `schemas.py`: `Track`, `MediaFile`, `AuditReport`, `CleanPlan`, etc.

### `core/`

- `config.py`: helpers tipados para claves propias,
- `exceptions.py`: excepciones específicas de la app.

## Flujo de limpieza

```text
ui.workflows.run_clean_workflow()
  -> carga configuración
  -> abre BrowserMenu
  -> ejecuta la auditoría sobre la selección
  -> muestra el resumen y pide confirmación para continuar
  -> genera planes desde los archivos ya auditados
  -> revisa selección global en ui.clean_menu
  -> confirma cambios
  -> ejecuta remux y renderiza resultado
```

## Reglas de dependencia

Permitido:

- `ui` -> `services`
- `services` -> `data`, `models`
- `data` -> `models`, `core`
- `main.py` -> todas las capas para hacer wiring

No permitido:

- `services` -> `questionary`, `rich`, `show_*`
- `models` -> `services`, `data`, `ui`
- `data` -> renderizado o prompts

## Ejemplo correcto

```python
plans = service.build_clean_plans_from_media_files(media_files, keep_languages)
final_plans = ask_global_clean_plans(plans)
```

## Ejemplo incorrecto

```python
class MediaService:
    def run(self) -> None:
        show_warning("Cancelado")
        questionary.confirm("¿Aplicar cambios?").ask()
```

## Puntos de extensión

Se puede ampliar el proyecto añadiendo:

- nuevos reportes sobre `AuditReport`,
- nuevas políticas de limpieza en `CleanService`,
- nuevos flujos UI,
- nuevos adaptadores en `data/` si cambia la herramienta externa.
