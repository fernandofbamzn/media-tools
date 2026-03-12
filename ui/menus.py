"""
Menús interactivos con Questionary.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

import questionary
from questionary import Choice

from models.schemas import BrowseResult


VIDEO_EXTENSIONS = {".mkv", ".mp4", ".m4v"}

logger = logging.getLogger(__name__)


class BaseMenu:
    """Clase base para menús de la aplicación."""

    def ask_select(
        self,
        message: str,
        choices: List[Choice],
    ) -> Optional[str]:
        """Lanza un selector interactivo con flechas."""
        return questionary.select(
            message,
            choices=choices,
            use_shortcuts=False,
            instruction="Usa flechas, Enter para elegir",
        ).ask()


def list_entries(current: Path) -> Tuple[List[Path], List[Path]]:
    """Lista directorios y archivos multimedia visibles en una carpeta."""
    dirs: List[Path] = []
    files: List[Path] = []

    for item in sorted(current.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
        if item.is_dir():
            dirs.append(item)
        elif item.is_file() and item.suffix.lower() in VIDEO_EXTENSIONS:
            files.append(item)

    return dirs, files


class BrowserMenu(BaseMenu):
    """Menú de navegación por árbol de carpetas."""

    def browse(self, root: Path) -> Optional[BrowseResult]:
        """Navega desde una raíz y permite elegir carpeta o archivo."""
        current = root.resolve()

        while True:
            breadcrumb = str(current)

            try:
                dirs, files = list_entries(current)
            except (PermissionError, FileNotFoundError, NotADirectoryError):
                logger.warning("No se pudo abrir la ruta de navegación: %s", current)
                choices: List[Choice] = []

                if current != root:
                    choices.append(Choice(title="⬅ Volver atrás", value=("up", current.parent)))

                choices.append(Choice(title="❌ Cancelar", value=("cancel", None)))

                result = self.ask_select(
                    message=(
                        f"Navegación > {breadcrumb}\n"
                        "No se pudo abrir esta ruta (permisos o ruta inválida)."
                    ),
                    choices=choices,
                )

                if result is None:
                    return None

                action, path = result

                if action == "up":
                    current = path
                    continue

                return None

            choices: List[Choice] = [
                Choice(title=f"✅ Seleccionar esta carpeta: {current.name or str(current)}", value=("select_dir", current)),
            ]

            if current != root:
                choices.append(Choice(title="⬆ Subir un nivel", value=("up", current.parent)))

            for directory in dirs:
                choices.append(Choice(title=f"📁 {directory.name}", value=("enter", directory)))

            for file_path in files:
                choices.append(Choice(title=f"🎬 {file_path.name}", value=("select_file", file_path)))

            choices.append(Choice(title="❌ Cancelar", value=("cancel", None)))

            result = self.ask_select(
                message=f"Navegación > {breadcrumb}",
                choices=choices,
            )

            if result is None:
                return None

            action, path = result

            if action == "select_dir":
                return BrowseResult(selected_path=path, selection_type="directory")

            if action == "select_file":
                return BrowseResult(selected_path=path, selection_type="file")

            if action == "up":
                current = path
                continue

            if action == "enter":
                current = path
                continue

            if action == "cancel":
                return None
