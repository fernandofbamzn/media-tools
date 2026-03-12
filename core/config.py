"""
Configuración XDG Base Directory.
"""

import os
from pathlib import Path

APP_NAME = "media-tools"

XDG_CONFIG = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
CONFIG_DIR = XDG_CONFIG / APP_NAME

CONFIG_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = CONFIG_DIR / "config.json"
