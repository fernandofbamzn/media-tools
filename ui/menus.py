"""
Menús interactivos con Questionary.
"""

from pathlib import Path
from typing import List, Literal, Optional, Tuple

import questionary
from questionary import Choice

from models.schemas import BrowseResult


VIDEO_EXTENSIONS = {".mkv", ".mp4", ".m4v"}
MenuAction = Literal["select_dir", "up", "enter", "select_file", "cancel"]
MenuSelection = Tuple[MenuAction, Optional[Path]]


class BaseMenu:
    """Clase base para menús de la aplicación."""

    def ask_select(
        self,
        message: str,
        choices: List[Choice],
    ) -> Optional[MenuSelection]:
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
            dirs, files = list_entries(current)
            breadcrumb = str(current)

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

            selection: Optional[MenuSelection] = self.ask_select(
                message=f"Navegación > {breadcrumb}",
                choices=choices,
            )

            if selection is None:
                return None

            action, selected_path = selection

            if action == "select_dir" and selected_path is not None:
                return BrowseResult(selected_path=selected_path, selection_type="directory")

            if action == "select_file" and selected_path is not None:
                return BrowseResult(selected_path=selected_path, selection_type="file")

            if action == "up" and selected_path is not None:
                current = selected_path
                continue

            if action == "enter" and selected_path is not None:
                current = selected_path
                continue

            if action == "cancel":
                return None
