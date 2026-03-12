#!/opt/media-tools/.venv/bin/python
"""
Entrypoint CLI según Guía Maestra CLI.
"""

import sys
from typing import Optional

import typer
from rich.console import Console

from core.config import load_media_root
from core.dependency_check import check_and_install
from core.exceptions import ConfigurationError
from models.schemas import BrowseResult
from services.business_logic import MediaToolsService
from ui.components import render_audit_summary, render_browse_result, render_doctor_result
from ui.doc_viewer import show_docs
from ui.menus import BrowserMenu

console = Console()
app = typer.Typer(help="Media Tools CLI profesional")


def _build_service() -> MediaToolsService:
    """Construye el servicio principal con configuración validada."""
    media_root = load_media_root()
    return MediaToolsService(default_root=media_root)


def _resolve_browse_selection(service: MediaToolsService) -> Optional[BrowseResult]:
    """Resuelve una selección interactiva desde la capa UI."""
    menu = BrowserMenu()
    return service.browse_service.browse(service.default_root, menu)


@app.command()
def doctor() -> None:
    """Diagnóstico del sistema."""
    service = _build_service()
    render_doctor_result(service.doctor())


@app.command()
def browse() -> None:
    """Navegación interactiva de biblioteca."""
    service = _build_service()
    selected = _resolve_browse_selection(service)
    render_browse_result(service.browse(selected))


@app.command()
def audit() -> None:
    """Auditoría de biblioteca."""
    service = _build_service()
    selected = _resolve_browse_selection(service)
    render_audit_summary(service.audit(selected))


@app.command()
def docs() -> None:
    """Abrir documentación integrada."""
    show_docs()


def main() -> None:
    """Punto de entrada principal."""

    # ✔ comprobación silenciosa de dependencias
    check_and_install()

    try:
        app()
    except ConfigurationError as exc:
        console.print(f"[red]Error de configuración: {exc}[/]")
        sys.exit(2)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelado por el usuario[/]")
        sys.exit(0)
    except Exception as exc:
        console.print(f"[red]Error inesperado: {exc}[/]")
        sys.exit(1)


if __name__ == "__main__":
    main()
