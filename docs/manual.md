# Manual de Uso

Guía operativa de `media-tools` para uso diario.

## 1. Preparación

1. Revisa [`requisitos.md`](requisitos.md).
2. Activa el entorno virtual si aplica.
3. Comprueba que `mkvmerge` está disponible.

## 2. Configurar `media_root`

Opciones admitidas:

- temporal: variable de entorno `MEDIA_TOOLS_MEDIA_ROOT`,
- persistente: `~/.config/media-tools/config.json`.

Ejemplo:

```json
{
  "media_root": "/srv/media",
  "keep_languages": ["spa", "eng", "es", "en"]
}
```

La carga valida que la ruta exista, sea directorio y tenga permisos de lectura. Si falla, la app prueba el directorio actual como fallback.

## 3. Arrancar la aplicación

```bash
python main.py
```

## 4. Menú principal

Opciones de negocio:

- `Navegar Biblioteca`
- `Auditoría`
- `Limpiar Pistas`

Opciones heredadas de `clibaseapp`:

- `Doctor`
- `Config`
- `Docs`
- `Actualizar App`

Nota: `Actualizar App` solo funciona si la herramienta se ejecuta desde un clon Git válido.

## 5. Flujo de auditoría

1. entra en `Auditoría`,
2. selecciona un archivo o carpeta,
3. revisa el árbol de pistas y el resumen global,
4. identifica idiomas faltantes o duplicados probables.

Ejemplo de uso:

```text
Inicio -> Auditoría
-> seleccionar /srv/media/Peliculas
-> revisar idiomas de audio y subtítulos
```

## 6. Flujo de limpieza

1. entra en `Limpiar Pistas`,
2. añade idiomas extra si hace falta,
3. selecciona la carpeta o archivo,
4. revisa el checklist global de pistas,
5. revisa el resumen por archivo,
6. confirma la operación destructiva,
7. espera al remux y revisa el resultado final.

Ejemplo de sesión:

```text
Idiomas a conservar: spa, eng
Añadir para esta ejecución: ita
Seleccionar carpeta: /srv/media/Series
Revisar plan
Confirmar cambios
```

## 7. Buenas prácticas operativas

- empezar por un único archivo o carpeta pequeña,
- conservar copia de seguridad si el material es crítico,
- revisar siempre el resumen antes de confirmar,
- no ejecutar cambios masivos sin una auditoría previa.

## 8. Problemas frecuentes

### No se encuentran archivos

- revisa `media_root`,
- confirma que la ruta contiene `mkv`, `mp4` o `m4v`,
- comprueba permisos de lectura.

### Falta `mkvmerge`

- instala `mkvtoolnix`,
- verifica el binario con `mkvmerge --version`.

### La actualización no está disponible

La opción `Actualizar App` mostrará un aviso si la app se instaló vía `pip` o desde un paquete sin repositorio Git.
