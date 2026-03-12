# Requisitos

Requisitos técnicos para ejecutar y desarrollar `media-tools`.

## Sistema operativo

- Linux (recomendado Debian/Ubuntu)

## Runtime

- Python 3.10 o superior

## Dependencias del sistema

- `mkvmerge` (paquete `mkvtoolnix`)
- `ffmpeg`
- `mediainfo`

Verificación rápida:

```bash
python3 --version
mkvmerge --version
ffmpeg -version
mediainfo --Version
```

## Dependencias Python

Paquetes principales:

- `typer`
- `rich`
- `questionary`
- `pydantic`

Instalación recomendada:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Notas de entorno

- Para bibliotecas grandes, usar discos/montajes con permisos de lectura/escritura claros.
- En contenedores, validar acceso a rutas bind/NFS antes de ejecutar acciones de escritura.
