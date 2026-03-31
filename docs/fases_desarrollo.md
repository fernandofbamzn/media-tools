# Fases de Desarrollo

Estado resumido del proyecto y de su hoja de ruta.

## Estado actual

| Fase | Objetivo | Estado |
| --- | --- | --- |
| 1 | Base del proyecto y wiring inicial | Completada |
| 2 | Navegación y auditoría integradas en el flujo de limpieza | Completada |
| 3 | Limpieza de pistas con revisión previa | Completada |
| 4 | Optimización de vídeo | Pendiente |
| 5 | Automatización y modo headless | Pendiente |

## Detalle por fase

### Fase 1. Base del proyecto

Incluyó:

- estructura por capas,
- entrypoint interactivo,
- gestión de configuración,
- documentación inicial.

### Fase 2. Navegación y auditoría integradas

Incluyó:

- navegación de archivos,
- análisis de metadatos,
- informes agregados,
- detección de duplicados probables,
- integración posterior dentro de la utilidad única de limpieza.

### Fase 3. Limpieza de pistas

Incluyó:

- consolidación del flujo de trabajo en una sola utilidad,
- generación de planes de limpieza,
- revisión interactiva,
- remux con `mkvmerge`,
- resumen final y cálculo de espacio recuperado.

### Fase 4. Optimización de vídeo

Objetivos previstos:

- transcodificación opcional,
- perfiles configurables,
- estimación de ahorro,
- perfil custom guiado con recomendaciones y tradeoffs visibles.

### Fase 5. Automatización

Objetivos previstos:

- ejecución no interactiva,
- salida JSON,
- códigos de salida pensados para scripts y CI.
