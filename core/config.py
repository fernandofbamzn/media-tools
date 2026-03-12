"""Configuración central de la aplicación."""

import json
import logging
import os
from pathlib import Path

from core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

APP_NAME = "media-tools"
ENV_MEDIA_ROOT = "MEDIA_TOOLS_MEDIA_ROOT"
DEFAULT_MEDIA_ROOT = Path("/mnt/Filmoteca")

XDG_CONFIG = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
CONFIG_DIR = XDG_CONFIG / APP_NAME

CONFIG_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = CONFIG_DIR / "config.json"


def _read_config_file(config_file: Path = CONFIG_FILE) -> dict:
    """Lee `config.json`; retorna diccionario vacío si no existe."""
    try:
        if not config_file.exists():
            return {}
        with config_file.open("r", encoding="utf-8") as handler:
            return json.load(handler)
    except json.JSONDecodeError as exc:
        message = (
            f"El archivo de configuración '{config_file}' no contiene JSON válido. "
            "Corrige el formato o elimina el archivo para regenerarlo."
        )
        logger.error(message)
        raise ConfigurationError(message) from exc
    except OSError as exc:
        message = f"No se pudo leer el archivo de configuración '{config_file}': {exc}"
        logger.error(message)
        raise ConfigurationError(message) from exc


def _validate_media_root(path: Path, source: str) -> Path:
    """Valida existencia y permisos de lectura de la ruta de biblioteca."""
    resolved_path = path.expanduser()

    if not resolved_path.exists():
        raise ConfigurationError(
            f"La ruta '{resolved_path}' definida en {source} no existe."
        )

    if not resolved_path.is_dir():
        raise ConfigurationError(
            f"La ruta '{resolved_path}' definida en {source} no es un directorio."
        )

    if not os.access(resolved_path, os.R_OK):
        raise ConfigurationError(
            f"La ruta '{resolved_path}' definida en {source} no tiene permisos de lectura."
        )

    return resolved_path


def load_media_root(config_file: Path = CONFIG_FILE) -> Path:
    """Carga `media_root` desde entorno/config con fallback explícito y validación."""
    configured_root = os.getenv(ENV_MEDIA_ROOT)
    source = f"variable de entorno {ENV_MEDIA_ROOT}"

    if configured_root is None:
        config_data = _read_config_file(config_file)
        configured_root = config_data.get("media_root")
        source = f"archivo de configuración {config_file}"

    if configured_root:
        try:
            return _validate_media_root(Path(configured_root), source)
        except ConfigurationError as exc:
            fallback_source = f"fallback por defecto {DEFAULT_MEDIA_ROOT}"
            try:
                fallback_path = _validate_media_root(DEFAULT_MEDIA_ROOT, fallback_source)
                logger.warning("%s Se utiliza fallback '%s'.", exc, fallback_path)
                return fallback_path
            except ConfigurationError as fallback_exc:
                message = (
                    f"Configuración inválida para media_root. {exc} "
                    f"Además, el fallback '{DEFAULT_MEDIA_ROOT}' también es inválido: {fallback_exc}"
                )
                logger.error(message)
                raise ConfigurationError(message) from fallback_exc

    try:
        return _validate_media_root(
            DEFAULT_MEDIA_ROOT, f"fallback por defecto {DEFAULT_MEDIA_ROOT}"
        )
    except ConfigurationError as exc:
        message = (
            f"No se configuró media_root y el fallback '{DEFAULT_MEDIA_ROOT}' no es válido: {exc}"
        )
        logger.error(message)
        raise ConfigurationError(message) from exc
