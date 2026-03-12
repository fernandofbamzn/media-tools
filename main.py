"""#!/opt/media-tools/.venv/bin/python"""
"""
Entrypoint CLI según Guía Maestra CLI.
"""

import sys
from pathlib import Path
from typing import Optional

import questionary
import typer
from rich.console import Console

from core.config import CONFIG_FILE, load_media_root, update_config
from core.dependency_check import check_and_install
from core.exceptions import ConfigurationError, MediaToolsError
from models.schemas import BrowseResult
from services.business_logic import MediaToolsService
from ui.components import (
    render_audit_summary,
    render_browse_result,
    render_doctor_result,
    show_header,
    show_info,
    show_success,
    show_warning,
)
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


@app.command()
def config() -> None:
    """Abre el editor de configuración interactivo."""
    show_header("Configuración de Media Tools", "Inicio > Configuración")

    current_root = load_media_root()
    show_info(f"Raíz multimedia actual: {current_root}")
    show_info(f"Archivo de configuración: {CONFIG_FILE}")

    action = questionary.select(
        "¿Qué deseas hacer?",
        choices=[
            "Modificar raíz multimedia (media_root)",
            "Salir"
        ]
    ).ask()

    if action == "Modificar raíz multimedia (media_root)":
        new_path_str = questionary.path(
            "Introduce la nueva ruta para la biblioteca:",
            default=str(current_root)
        ).ask()

        if new_path_str:
            new_path = Path(new_path_str).expanduser().resolve()
            if not new_path.exists():
                show_warning(f"La ruta '{new_path}' no existe. Se guardará de todos modos.")

            update_config("media_root", str(new_path))
            show_success(f"La raíz multimedia se ha actualizado correctamente a: {new_path}")
        else:
            show_warning("Operación cancelada.")
    else:
        show_info("Saliendo sin guardar cambios.")


def main() -> None:
    """Punto de entrada principal."""

    # ✔ comprobación silenciosa de dependencias
    check_and_install()

    try:
        app()
    except ConfigurationError as exc:
        console.print(f"[red]Error de configuración: {exc}[/]")
        sys.exit(2)
    except MediaToolsError as exc:
        console.print(f"[red]Error operativo: {exc}[/]")
        sys.exit(3)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelado por el usuario[/]")
        sys.exit(0)
    except Exception as exc:
        console.print(f"[red]Error inesperado: {exc}[/]")
        sys.exit(1)


if __name__ == "__main__":
    main()
