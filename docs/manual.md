# Manual de Uso

Guía operativa para ejecutar `media-tools` de forma segura.

## 1. Preparación

1. Confirmar requisitos: `docs/requisitos.md`.
2. Activar entorno virtual (si aplica).
3. Verificar disponibilidad de binarios externos.

## 1.1 Configurar `media_root`

Antes de navegar o auditar, define la raíz de tu biblioteca:

- **Opción A (recomendada en terminal):** variable de entorno `MEDIA_TOOLS_MEDIA_ROOT`.
- **Opción B (persistente):** `~/.config/media-tools/config.json` con clave `media_root`.

Ejemplo:

```json
{
  "media_root": "/srv/media"
}
```

Validaciones aplicadas al cargar configuración:

- la ruta debe existir
- debe ser directorio
- debe tener permisos de lectura

Si falla la ruta configurada, la CLI intenta `/mnt/Filmoteca` como fallback explícito y muestra un error claro si tampoco es válida.

## 2. Ejecución

Comando principal:

```bash
media-tools
```

## 3. Flujo recomendado

1. Seleccionar ruta (archivo o carpeta).
2. Ejecutar análisis de pistas.
3. Revisar duplicados e idiomas detectados.
4. Configurar cambios deseados.
5. Revisar informe previo.
6. Confirmar explícitamente antes de aplicar cambios.

## 4. Buenas prácticas operativas

- Empezar por carpetas pequeñas de prueba.
- Conservar backups de material crítico.
- Revisar el informe antes de confirmar.
- Evitar operaciones destructivas en lotes grandes sin validación previa.

## 5. Solución de problemas rápida

- Si faltan binarios (`mkvmerge`, `ffmpeg`, `mediainfo`), revisar instalación del sistema.
- Si hay errores de permisos, validar usuario, grupo y montaje.
- Si no se detectan archivos, comprobar extensión y ruta seleccionada.
