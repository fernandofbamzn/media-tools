# Requisitos

Requisitos técnicos para ejecutar y mantener `media-tools`.

## Sistema operativo

- Linux recomendado para uso real.
- Windows puede servir para desarrollo y pruebas locales.

## Python

- Python `3.10+`

Comprobación rápida:

```bash
python --version
```

## Binarios del sistema

Dependencias del sistema:

- `mkvmerge` obligatorio
- `ffmpeg` recomendado
- `mediainfo` recomendado

Verificación:

```bash
mkvmerge --version
ffmpeg -version
mediainfo --Version
```

## Dependencias Python

Instalación recomendada:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Requisitos para desarrollo

Ejecutar tests:

```bash
python -m pytest -q
```

Si el entorno tiene plugins globales de `pytest`, usar:

```bash
set PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
python -m pytest -q
```

## Validaciones previas recomendadas

Antes de limpiar archivos:

1. comprobar que `media_root` existe,
2. validar permisos de lectura y escritura,
3. confirmar que `mkvmerge` está accesible en `PATH`,
4. empezar por una carpeta pequeña de prueba.

## Ejemplo de entorno válido

```text
Python 3.12
mkvmerge instalado
ffmpeg instalado
mediainfo instalado
config.json con media_root apuntando a /srv/media
```
