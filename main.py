#!/opt/media-tools/.venv/bin/python
"""
Entrypoint CLI según Guía Maestra CLI.
"""

import sys

import typer
from rich.console import Console

from core.dependency_check import check_and_install
from services.business_logic import MediaToolsService
from ui.doc_viewer import show_docs

console = Console()
app = typer.Typer(help="Media Tools CLI profesional")


@app.command()
def doctor() -> None:
    """Diagnóstico del sistema."""
    MediaToolsService().doctor()


@app.command()
def browse() -> None:
    """Navegación interactiva de biblioteca."""
    MediaToolsService().browse()


@app.command()
def audit() -> None:
    """Auditoría de biblioteca."""
    MediaToolsService().audit()


@app.command()
def docs() -> None:
    """Abrir documentación integrada."""
    show_docs()


def main() -> None:
    """
    Punto de entrada principal.
    """

    # ✔ comprobación silenciosa de dependencias
    check_and_install()

    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelado por el usuario[/]")
        sys.exit(0)
    except Exception as exc:
        console.print(f"[red]Error inesperado: {exc}[/]")
        sys.exit(1)


if __name__ == "__main__":
    main()
