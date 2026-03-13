"""
Configuración específica de media-tools.

Delega la persistencia y validación al ConfigManager de clibaseapp.
Solo expone helpers tipados para las claves propias de la app.
"""

from pathlib import Path
from typing import List

from clibaseapp import ConfigManager

DEFAULT_KEEP_LANGUAGES = ["spa", "eng", "es", "en"]
"""Idiomas que se conservan por defecto en los planes de limpieza."""


def load_media_root(config: ConfigManager) -> Path:
    """Carga `media_root` desde env -> config -> cwd.

    La validación física de la ruta la delega `ConfigManager.load_path()`.
    """

    return config.load_path("media_root", env_var="MEDIA_TOOLS_MEDIA_ROOT", fallback=Path.cwd())


def load_keep_languages(config: ConfigManager) -> List[str]:
    """Carga los idiomas a mantener por defecto.

    Si la clave todavía no existe, persiste el conjunto por defecto para
    que la app quede inicializada de forma consistente.
    """

    languages = config.get("keep_languages")
    if languages is None:
        config.update("keep_languages", DEFAULT_KEEP_LANGUAGES)
        return DEFAULT_KEEP_LANGUAGES.copy()
    return [str(language) for language in languages]
