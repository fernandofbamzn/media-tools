"""
Configuración específica de media-tools.
Delega todo el CRUD al ConfigManager de clibaseapp.
Solo define helpers de acceso a claves propias de la app.
"""

from pathlib import Path
from typing import List

from clibaseapp import ConfigManager


# Singleton del config manager de esta app
_config = ConfigManager(
    app_name="media-tools",
    default_config={
        "media_root": str(Path.cwd().resolve()),
        "keep_languages": ["spa", "eng", "es", "en"],
    },
)


def get_config() -> ConfigManager:
    """Devuelve el gestor de configuración de media-tools."""
    return _config


def load_media_root() -> Path:
    """Carga media_root desde env → config → cwd."""
    return _config.load_path("media_root", env_var="MEDIA_TOOLS_MEDIA_ROOT")


def load_keep_languages() -> List[str]:
    """Carga los idiomas a mantener por defecto."""
    langs = _config.get("keep_languages")
    if langs is None:
        default = ["spa", "eng", "es", "en"]
        _config.update("keep_languages", default)
        return default
    return langs
