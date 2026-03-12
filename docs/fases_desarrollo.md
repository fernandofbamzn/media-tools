# Fases de Desarrollo

Roadmap funcional del proyecto con alcance y estado.

## Fase 1 — Base del proyecto ✅

**Objetivo**: fundaciones técnicas de la CLI.

Incluye:

- estructura de carpetas por capas
- comandos base y arranque
- verificación inicial de dependencias
- documentación técnica mínima

**Estado**: completada.

## Fase 2 — Navegación y auditoría ✅

**Objetivo**: inspección fiable de bibliotecas multimedia.

Incluye:

- navegación interactiva de rutas
- lectura de metadata de medios
- auditoría de idiomas y códecs
- detección preliminar de duplicados

**Estado**: completada.

## Fase 3 — Lógica de negocio y Acciones sobre archivos 🚧

**Objetivo**: ejecutar acciones reales de limpieza y organizar pistas sobre los archivos multimedia.

Incluye:

- lógica para identificar pistas a conservar (ej: vídeo principal, audios predeterminados/español)
- eliminación (demux/remux) de audios y subtítulos innecesarios usando `mkvmerge`/`ffmpeg`
- resolución o aviso en caso de pistas conflictivas o duplicadas
- informe de las acciones tomadas y ahorro de espacio en el archivo final

**Estado**: en progreso.

## Fase 4 — Optimización de vídeo 🔭

**Objetivo**: reducción de tamaño con control de calidad.

Incluye:

- transcodificación opcional
- perfiles configurables
- estimación de ahorro de espacio

**Estado**: futuro.

## Fase 5 — Automatización / modo headless 🔭

**Objetivo**: integración en scripts y pipelines.

Incluye:

- ejecución no interactiva
- salida estructurada (JSON)
- códigos de salida robustos para CI/CD

**Estado**: futuro.
