~MEDIA TOOLS CLI
===============

Herramienta interactiva para limpieza y gestión de pistas multimedia.

FUNCIONES
---------

- Navegación interactiva por directorios
- Análisis de pistas con mkvmerge
- Eliminación de pistas duplicadas
- Filtrado de idiomas de audio
- Filtrado de subtítulos
- Transcodificación opcional con ffmpeg
- Informe previo antes de ejecutar

FLUJO DE USO
------------

1. Ejecutar el programa

   media-tools

2. Seleccionar carpeta o archivo

3. Elegir opciones de limpieza

4. Revisar informe

5. Confirmar ejecución

MODOS DE SEGURIDAD
------------------

Modo simulación (recomendado).

No modifica archivos, solo muestra lo que haría.

RUTAS IMPORTANTES
-----------------

Script principal:
/opt/media-tools/media_tools_cli.py

Comando del sistema:
/usr/local/bin/media-tools

EJEMPLOS DE USO
---------------

Procesar una serie:

/Filmoteca/Series/ONE PIECE (2023)/

Procesar un episodio concreto:

/Filmoteca/.../S02E01.mkv
