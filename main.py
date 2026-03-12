"""#!/opt/media-tools/.venv/bin/python"""
"""
Entrypoint CLI según Guía Maestra CLI.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import questionary
import typer
from rich.console import Console

from core.config import CONFIG_FILE, load_keep_languages, load_media_root, update_config
from core.dependency_check import check_and_install
from core.exceptions import ConfigurationError, MediaToolsError
from models.schemas import ActionType, BrowseResult
from services.business_logic import MediaToolsService
from ui.components import (
    clear_screen,
    pause,
    render_audit_summary,
    render_browse_result,
    render_doctor_result,
    show_header,
    show_info,
    show_success,
    show_warning,
)
from ui.clean_menu import ask_global_clean_plans
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
def clean(target: Optional[Path] = typer.Argument(None, help="Ruta a limpiar (opcional, interactivo si se omite)")) -> None:
    """Planifica y limpia pistas de audio o subtítulos no deseadas."""
    service = _build_service()
    clear_screen()
    show_header("Limpiador de Pistas", "Inicio > Limpieza", icon="🧹")

    base_langs = load_keep_languages()
    extra_str = questionary.text(
        f"Idiomas a conservar por defecto: {', '.join(base_langs)}.\n¿Añadir idiomas para ESTA ejecución? (ej: jpn, por, fre - vacío para ninguno):",
    ).ask()

    if extra_str is None:
        return

    extra_langs = [l.strip().lower() for l in extra_str.split(",") if l.strip()]
    keep_languages = base_langs + extra_langs

    selected = _resolve_browse_selection(service, target)
    if not selected:
        show_warning("Selección cancelada.")
        return

    plans = service.build_clean_plans(selected, keep_languages)
    if not plans:
        show_warning("No se encontraron archivos multimedia para limpiar.")
        return

    try:
        final_plans = ask_global_clean_plans(plans)
    except KeyboardInterrupt:
        show_warning("\nProceso de planificación cancelado por el usuario.")
        return

    clear_screen()
    show_header("Resumen del Plan de Limpieza", "Inicio > Limpieza > Resumen", icon="📝")
    for p in final_plans:
        to_keep = sum(1 for a in p.track_actions if a.action == ActionType.KEEP)
        to_remove = sum(1 for a in p.track_actions if a.action == ActionType.REMOVE)
        show_info(f"🎬 {p.media_file.path.name}")
        console.print(f"   [green]+ Conservar: {to_keep} pistas[/green] | [red]- Eliminar: {to_remove} pistas[/red]")
        console.print()

    show_success("Planificación confirmada. (Nota: Ejecución real pendiente de implementar).")


@app.command()
def config() -> None:
    """Abre el editor de configuración interactivo."""
    clear_screen()
    show_header("Configuración de Media Tools", "Inicio > Configuración", icon="⚙️")

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


def check_for_updates() -> None:
    """Realiza un git pull y reinicia la aplicación si hay cambios."""
    clear_screen()
    show_header("Actualización de la Aplicación", icon="🔄")
    show_info("Buscando actualizaciones en el repositorio remoto...")

    try:
        result = subprocess.run(
            ["git", "pull"],
            capture_output=True,
            text=True,
            check=True,
            cwd=str(Path(__file__).parent)
        )
        
        output = result.stdout.strip()
        console.print(f"[dim]{output}[/dim]")

        if "Already up to date." in output or "Ya está actualizado." in output:
            show_success("La aplicación ya está en la última versión.")
        else:
            show_warning("¡La aplicación se ha actualizado! Reiniciando automáticamente...")
            
            # Limpiamos y recreamos el proceso desde 0 usando el interprete actual (venv)
            os.execv(sys.executable, [sys.executable] + sys.argv)
            
    except subprocess.CalledProcessError as exc:
        show_error(f"Error al actualizar desde git: {exc.stderr}")
    except FileNotFoundError:
        show_error("Comando 'git' no encontrado en el sistema.")
    except Exception as exc:
        show_error(f"Error inesperado al intentar actualizar: {exc}")


@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context) -> None:
    """Media Tools CLI profesional."""
    if ctx.invoked_subcommand is None:
        _interactive_main_menu()


def _interactive_main_menu() -> None:
    """Menú interactivo principal cuando no se proveen comandos."""
    while True:
        clear_screen()
        show_header("Media Tools", "Inicio", icon="⚡")

        choice = questionary.select(
            "Selecciona una opción:",
            choices=[
                questionary.Choice("🎬 Navegar Biblioteca (browse)", value="browse"),
                questionary.Choice("🧹 Limpiar Pistas (clean)", value="clean"),
                questionary.Choice("🔍 Auditoría (audit)", value="audit"),
                questionary.Choice("🩺 Diagnóstico (doctor)", value="doctor"),
                questionary.Choice("⚙️ Configuración (config)", value="config"),
                questionary.Choice("📖 Documentación (docs)", value="docs"),
                questionary.Choice("🔄 Actualizar App (update)", value="update"),
                questionary.Choice("❌ Salir", value="exit"),
            ]
        ).ask()

        if choice == "browse":
            browse(None)
            pause()
        elif choice == "clean":
            clean(None)
            pause()
        elif choice == "audit":
            audit(None)
            pause()
        elif choice == "doctor":
            doctor()
            pause()
        elif choice == "config":
            config()
            pause()
        elif choice == "docs":
            docs()
            pause()
        elif choice == "update":
            check_for_updates()
            pause()
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
