# media-tools

`media-tools` es una CLI para inspeccionar bibliotecas multimedia, auditar pistas y preparar limpiezas seguras de archivos `MKV`, `MP4` y `M4V`.

## Capacidades actuales

- Navega bibliotecas multimedia desde terminal.
- Analiza metadatos de audio, vídeo y subtítulos con `mkvmerge`.
- Genera informes de auditoría por idiomas y códecs.
- Construye planes de limpieza de pistas.
- Ejecuta cambios destructivos solo tras confirmación explícita.

## Arquitectura en una línea

`main.py -> ui/ -> services/ -> data/ -> models/`

La capa `ui/` contiene prompts, menús y renderizado. La capa `services/` contiene lógica pura y no imprime nada en consola.

## Inicio rápido

Crear entorno e instalar dependencias:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Arrancar la aplicación:

```bash
python main.py
```

## Configuración base

La raíz multimedia se resuelve con esta prioridad:

1. variable de entorno `MEDIA_TOOLS_MEDIA_ROOT`,
2. clave `media_root` en `~/.config/media-tools/config.json`,
3. directorio actual como fallback.

Ejemplo de `config.json`:

```json
{
  "media_root": "/srv/media",
  "keep_languages": ["spa", "eng", "es", "en"]
}
```

## Ejemplos de uso habituales

Abrir la app y navegar la biblioteca:

```bash
python main.py
```

Flujo recomendado dentro del menú:

1. `Navegar Biblioteca`
2. `Auditoría`
3. `Limpiar Pistas`
4. revisar el resumen
5. confirmar cambios

Configuración temporal por sesión:

```bash
set MEDIA_TOOLS_MEDIA_ROOT=D:\Media
python main.py
```

## Documentación del proyecto

- [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md): contexto de producto y restricciones.
- [`docs/requisitos.md`](docs/requisitos.md): requisitos del sistema y del entorno Python.
- [`docs/manual.md`](docs/manual.md): guía de uso paso a paso.
- [`docs/arquitectura.md`](docs/arquitectura.md): capas, dependencias y flujos.
- [`docs/dev_rules.md`](docs/dev_rules.md): reglas de implementación obligatorias.
- [`docs/guia_desarrollo.md`](docs/guia_desarrollo.md): guía práctica para desarrollar sobre el proyecto.
- [`docs/fases_desarrollo.md`](docs/fases_desarrollo.md): estado funcional y próximos hitos.
