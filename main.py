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


def _resolve_browse_selection(service: MediaToolsService, target: Optional[Path] = None) -> Optional[BrowseResult]:
    """Resuelve una selección interactiva desde la capa UI o desde un argumento."""
    if target:
        resolved = target.expanduser().resolve()
        if not resolved.exists():
            show_error(f"La ruta especificada no existe: {resolved}")
            raise typer.Exit(1)
        sel_type = "file" if resolved.is_file() else "directory"
        return BrowseResult(selected_path=resolved, selection_type=sel_type)

    menu = BrowserMenu()
    return service.browse_service.browse(service.default_root, menu)


@app.command()
def doctor() -> None:
    """Diagnóstico del sistema."""
    service = _build_service()
    render_doctor_result(service.doctor())


@app.command()
def browse(target: Optional[Path] = typer.Argument(None, help="Ruta a inspeccionar (opcional, interactivo si se omite)")) -> None:
    """Navegación interactiva de biblioteca."""
    service = _build_service()
    selected = _resolve_browse_selection(service, target)
    render_browse_result(service.browse(selected))


@app.command()
def audit(target: Optional[Path] = typer.Argument(None, help="Ruta a auditar (opcional, interactivo si se omite)")) -> None:
    """Auditoría de biblioteca."""
    service = _build_service()
    selected = _resolve_browse_selection(service, target)
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


@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context) -> None:
    """Media Tools CLI profesional."""
    if ctx.invoked_subcommand is None:
        _interactive_main_menu()


def _interactive_main_menu() -> None:
    """Menú interactivo principal cuando no se proveen comandos."""
    show_header("Media Tools", "Inicio")

    while True:
        choice = questionary.select(
            "Selecciona una opción:",
            choices=[
                questionary.Choice("Navegar Biblioteca (browse)", value="browse"),
                questionary.Choice("Auditoría (audit)", value="audit"),
                questionary.Choice("Diagnóstico (doctor)", value="doctor"),
                questionary.Choice("Configuración (config)", value="config"),
                questionary.Choice("Documentación (docs)", value="docs"),
                questionary.Choice("Salir", value="exit"),
            ]
        ).ask()

        if choice == "browse":
            browse(None)
        elif choice == "audit":
            audit(None)
        elif choice == "doctor":
            doctor()
        elif choice == "config":
            config()
        elif choice == "docs":
            docs()
        else:
            show_info("¡Hasta la próxima!")
            break


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
