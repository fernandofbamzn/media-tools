"""
Servicio de navegación interactiva.
"""

from pathlib import Path
from typing import Optional

from models.schemas import BrowseResult
from ui.menus import BrowserMenu


class BrowseService:
    """Lógica de navegación de biblioteca."""

    def __init__(self, browser_menu: Optional[BrowserMenu] = None) -> None:
        self.browser_menu = browser_menu or BrowserMenu()

    def browse(self, root: Path) -> Optional[BrowseResult]:
        """Abre el navegador y devuelve la selección."""
        return self.browser_menu.browse(root)
