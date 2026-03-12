# Reglas de Desarrollo

Normas para implementar cambios sin degradar calidad, seguridad ni mantenibilidad.

## 1) Principios de implementación

- **Fail-fast**: validar precondiciones antes de actuar.
- **Idempotencia**: una operación repetida no debe corromper resultados.
- **No hardcoding**: rutas, perfiles y parámetros sensibles deben ser configurables.
- **Cambios pequeños**: preferir iteraciones cortas y revisables.

> Las responsabilidades por capa se documentan en `docs/arquitectura.md`.

## 2) Estilo de código

- Type hints obligatorios en APIs públicas.
- Docstrings en clases y métodos públicos.
- Funciones pequeñas y enfocadas (evitar >100 líneas salvo justificación clara).
- Nombres explícitos de variables y funciones.

## 3) Reglas por capa

- `ui/`: solo interacción y presentación.
- `services/`: lógica de negocio reutilizable y testeable.
- `data/`: acceso a recursos externos con patrón repositorio.
- `models/`: estructuras de datos simples.
- `core/`: configuración, excepciones y utilidades comunes.

## 4) Seguridad operativa

- Ninguna acción destructiva sin confirmación explícita del usuario.
- Validar permisos y disponibilidad de herramientas (`mkvmerge`, `ffmpeg`, `mediainfo`).
- Evitar exponer información sensible en logs.

## 5) Calidad y validación

Antes de integrar cambios:

1. Ejecutar checks/tests disponibles.
2. Verificar que no se rompe el flujo de capas.
3. Actualizar documentación afectada.
4. Registrar limitaciones o deuda técnica detectada.

## 6) Estrategia de cambio recomendada

Cuando una funcionalidad toca múltiples capas:

1. Modelos
2. Repositorio (`data/`)
3. Servicios
4. UI
5. CLI (`main.py`)
