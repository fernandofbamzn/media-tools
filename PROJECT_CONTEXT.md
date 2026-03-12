# Project Context

## Propósito

`media-tools` es una aplicación CLI para gestionar bibliotecas multimedia y preparar ediciones de forma segura y trazable.

## Entorno objetivo

- Linux (servidores domésticos y self-hosted).
- Contenedores LXC/Proxmox.
- Bibliotecas grandes montadas por NFS o bind mounts.

## Stack técnico

- Python 3
- Typer (CLI)
- Rich + Questionary (interfaz interactiva)
- mkvmerge, ffmpeg y mediainfo (herramientas externas)

## Principios no negociables

- Arquitectura por capas: `UI → Services → Repository → Models`.
- Confirmación explícita antes de cualquier acción destructiva.
- Operaciones idempotentes y enfoque fail-fast.
- Cero rutas o credenciales hardcodeadas.

## Navegación documental

Para detalles concretos consultar:

- Requisitos: `docs/requisitos.md`
- Arquitectura: `docs/arquitectura.md`
- Reglas de desarrollo: `docs/dev_rules.md`
- Roadmap: `docs/fases_desarrollo.md`
- Manual de uso: `docs/manual.md`
