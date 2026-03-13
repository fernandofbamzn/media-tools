# media-tools

CLI para analizar y planificar edición segura de archivos multimedia (MKV/MP4), orientada a bibliotecas grandes en Linux.

## Qué hace

- Inspección de archivos y pistas (audio/subtítulos).
- Detección de duplicados.
- Selección de idiomas.
- Generación de auditorías e informes previos.
- Preparación de cambios seguros (siempre con confirmación explícita).

La interacción CLI vive en `ui/`, mientras que `services/` queda reservada para lógica de negocio pura.

## Estado del proyecto

La hoja de ruta por fases vive en `docs/fases_desarrollo.md`.

## Inicio rápido

1. Revisar requisitos del entorno en `docs/requisitos.md`.
2. Revisar arquitectura en `docs/arquitectura.md`.
3. Revisar reglas de desarrollo en `docs/dev_rules.md`.
4. Usar la guía operativa en `docs/manual.md`.

## Estructura de documentación

- `PROJECT_CONTEXT.md`: contexto ejecutivo y decisiones de alto nivel.
- `docs/requisitos.md`: dependencias del sistema y entorno Python.
- `docs/arquitectura.md`: capas, responsabilidades y flujo técnico.
- `docs/dev_rules.md`: normas de implementación y calidad.
- `docs/fases_desarrollo.md`: roadmap por fases y estado.
- `docs/manual.md`: uso operativo de la herramienta.


## Configuración de `media_root`

La ruta base de la biblioteca multimedia se resuelve con esta prioridad:

1. Variable de entorno `MEDIA_TOOLS_MEDIA_ROOT`.
2. Clave `media_root` en `~/.config/media-tools/config.json`, gestionada por la instancia `self.config` heredada de `CLIBaseApp`.
3. Fallback explícito al directorio actual.

Ejemplo de `config.json`:

```json
{
  "media_root": "/srv/media"
}
```

La ruta configurada debe existir, ser un directorio y tener permisos de lectura.
Si la ruta configurada es inválida, se intenta el fallback y se reporta un error claro si también falla.
