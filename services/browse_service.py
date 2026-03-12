"""
Servicio de navegación desacoplado de la UI.
"""

from pathlib import Path
from typing import Optional, Protocol

from models.schemas import BrowseResult


class BrowseSelector(Protocol):
    """Puerto de navegación implementado por capa superior (UI)."""

    def browse(self, root: Path) -> Optional[BrowseResult]:
        """Resuelve una selección de archivo o carpeta."""


class BrowseService:
    """Lógica de navegación de biblioteca sin dependencias de UI."""

    def browse(self, root: Path, selector: BrowseSelector) -> Optional[BrowseResult]:
        """Delega la selección al adaptador recibido por inversión de dependencias."""
        return selector.browse(root)
