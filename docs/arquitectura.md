# Arquitectura del Proyecto

Documento técnico de referencia para la estructura interna de `media-tools`.

## Vista general

Arquitectura CLI modular (N-Tier):

```text
main.py → ui/ → services/ → data/ → models/
               ↘ core/ (config, validaciones, errores)
```

## Estructura

```text
media-tools/
├── main.py
├── core/
├── models/
├── services/
├── data/
├── ui/
├── docs/
└── scripts/
```

## Responsabilidades por capa

### `main.py`

- Registra comandos Typer.
- Inicializa servicios y wiring.
- Inyecta la única instancia de configuración (`self.config`) heredada de `CLIBaseApp`.
- Centraliza manejo global de errores.
- Ejecuta verificaciones de dependencias al arranque.

### `ui/`

- Renderizado con Rich.
- Menús e interacción con Questionary.
- Traducción de entradas/salidas de usuario.
- Workflows interactivos como `ui/workflows.py`.

> No contiene lógica de negocio.

### `services/`

- Casos de uso de negocio (auditoría, planificación, limpieza).
- Orquestación entre modelos y repositorios.
- Reglas de validación de dominio.
- Sin impresiones, prompts ni dependencias de `questionary`/`rich`.

> No hace I/O de consola ni solicita input directo.

### `data/`

- Adaptadores a filesystem y herramientas externas.
- Implementaciones Repository Pattern.
- Serialización/deserialización técnica.

### `models/`

- Entidades y DTOs tipados.
- Estructuras de datos sin lógica compleja.

### `core/`

- Configuración central.
- Excepciones personalizadas.
- utilidades transversales de infraestructura.

## Reglas de dependencia

Dependencia permitida (sentido único):

- `ui` depende de `services`
- `services` depende de `data` y `models`
- `data` depende de `models` y `core`
- `main.py` coordina todo

Dependencias a evitar:

- `services` → `ui`
- `models` → `ui` / `services` / `data`
- `ui` → herramientas externas directas
