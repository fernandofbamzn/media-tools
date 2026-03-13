# Contexto del Proyecto

## Propósito

`media-tools` existe para ayudar a mantener bibliotecas multimedia grandes con una CLI segura, trazable y usable en servidores domésticos o autohospedados.

## Entorno objetivo

- Linux como entorno principal de ejecución.
- Contenedores LXC o hosts Proxmox.
- Bibliotecas montadas mediante discos locales, bind mounts o NFS.

## Decisiones de diseño

- arquitectura por capas,
- confirmación explícita antes de modificar archivos,
- tipado estricto y modelos claros,
- dependencia fuerte de herramientas externas bien conocidas (`mkvmerge`, `ffmpeg`, `mediainfo`),
- configuración persistente reutilizando `ConfigManager` de `clibaseapp`.

## Objetivos funcionales actuales

- inspeccionar archivos multimedia,
- auditar idiomas y códecs,
- detectar duplicados probables,
- limpiar pistas innecesarias con revisión previa.

## No objetivos actuales

- transcodificación masiva,
- operación completamente headless,
- integración con bases de datos externas,
- reindexado de catálogos.

## Restricciones operativas

- no romper la separación `ui -> services -> data -> models`,
- no hardcodear rutas sensibles,
- no escribir sobre archivos sin confirmación,
- fallar pronto cuando falten binarios o permisos.

## Escenario de uso representativo

```text
Biblioteca montada en /srv/media
-> el operador audita una carpeta
-> revisa idiomas detectados
-> ajusta qué pistas conservar
-> confirma el plan
-> el remux se ejecuta con feedback de progreso
```
