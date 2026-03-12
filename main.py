"""
Entrypoint de Media Tools — hereda del framework clibaseapp.
"""

from pathlib import Path
from typing import Optional

import questionary
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from clibaseapp import CLIBaseApp, BrowserMenu, clear_screen, console, pause, show_header, show_info, show_success, show_warning, show_error
from core.config import load_keep_languages, load_media_root, update_config
from core.dependency_check import check_and_install
from models.schemas import ActionType, BrowseResult
from services.business_logic import MediaToolsService
from ui.components import render_audit_summary, render_browse_result, render_doctor_result
from ui.clean_menu import ask_global_clean_plans
from ui.doc_viewer import show_docs

VIDEO_EXTENSIONS = {".mkv", ".mp4", ".m4v"}


def _format_bytes(size: int) -> str:
    """Da formato a los bytes en humano legible (KB, MB, GB)."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:3.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


class MediaToolsApp(CLIBaseApp):
    """Aplicación CLI de gestión multimedia. Hereda de clibaseapp."""

    def __init__(self):
        super().__init__(
            app_name="media-tools",
            description="Media Tools CLI"
        )
        self.config.default_config = {
            "media_root": str(Path.cwd().resolve()),
            "keep_languages": ["spa", "eng", "es", "en"]
        }
        self.require_binaries(["mkvmerge"])

    def _build_service(self) -> MediaToolsService:
        media_root = load_media_root()
        return MediaToolsService(default_root=media_root)

    def _resolve_browse(self, target: Optional[Path] = None) -> Optional[BrowseResult]:
        if target:
            resolved = target.expanduser().resolve()
            if not resolved.exists():
                show_error(f"La ruta especificada no existe: {resolved}")
                return None
            sel_type = "file" if resolved.is_file() else "directory"
            return BrowseResult(selected_path=resolved, selection_type=sel_type)

        browser = BrowserMenu(file_extensions=VIDEO_EXTENSIONS, file_icon="🎬")
        result = browser.browse(load_media_root())
        if result:
            return BrowseResult(selected_path=result.selected_path, selection_type=result.selection_type)
        return None

    # ── Acciones de menú (callbacks) ──────────────────────────────

    def run_doctor(self):
        service = self._build_service()
        render_doctor_result(service.doctor())

    def run_browse(self):
        service = self._build_service()
        selected = self._resolve_browse()
        render_browse_result(service.browse(selected))

    def run_audit(self):
        service = self._build_service()
        selected = self._resolve_browse()
        render_audit_summary(service.audit(selected))

    def run_docs(self):
        show_docs()

    def run_config(self):
        clear_screen()
        show_header("Configuración de Media Tools", "Inicio > Configuración", icon="⚙️")

        current_root = load_media_root()
        show_info(f"Raíz multimedia actual: {current_root}")
        show_info(f"Archivo de configuración: {self.config.config_file}")

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

    def run_clean(self):
        service = self._build_service()
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

        selected = self._resolve_browse()
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
        total_to_remove = 0
        plans_to_execute = []

        for p in final_plans:
            to_keep = sum(1 for a in p.track_actions if a.action == ActionType.KEEP)
            to_remove = sum(1 for a in p.track_actions if a.action == ActionType.REMOVE)

            show_info(f"🎬 {p.media_file.path.name}")
            console.print(f"   [green]+ Conservar: {to_keep} pistas[/green] | [red]- Eliminar: {to_remove} pistas[/red]")
            console.print()

            if to_remove > 0:
                total_to_remove += to_remove
                plans_to_execute.append(p)

        if not plans_to_execute:
            show_success("Planificación completada: Los archivos ya cumplen con la selección actual. No hay pistas que borrar.")
            return

        console.print(f"[bold red]ATENCIÓN:[/] Se van a eliminar un total de [bold]{total_to_remove}[/] pistas en {len(plans_to_execute)} archivos.")
        do_execute = questionary.confirm("¿Deseas aplicar estos cambios y LIMPIAR los archivos?\n(Esta acción es destructiva sobre las pistas eliminadas)").ask()

        if not do_execute:
            show_warning("Ejecución cancelada por el usuario. No se ha modificado ningún archivo.")
            return

        total_saved = 0
        errors = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task_id = progress.add_task("Limpiando archivos...", total=len(plans_to_execute))

            for plan in plans_to_execute:
                progress.update(task_id, description=f"Limpiando: {plan.media_file.path.name}...")
                try:
                    saved = service.execute_clean_plan(plan)
                    total_saved += saved
                except Exception as e:
                    errors += 1
                    progress.console.print(f"[red]Error procesando {plan.media_file.path.name}: {e}[/]")
                progress.advance(task_id)

        clear_screen()
        show_header("✨ Limpieza Completada ✨", icon="🎉")

        msg = f"Archivos procesados: {len(plans_to_execute) - errors}/{len(plans_to_execute)}\n"
        msg += f"Espacio recuperado: {_format_bytes(total_saved)}"

        if errors == 0:
            show_success(msg)
        else:
            show_warning(f"{msg}\nHubo {errors} archivos con errores.")

    # ── Registro de comandos y menú ───────────────────────────────

    def setup_commands(self) -> None:
        """Registra las opciones de menú interactivas y los comandos CLI de Typer."""

        # Opciones del menú interactivo principal
        self.register_menu_option("🎬 Navegar Biblioteca (browse)", "browse", self.run_browse)
        self.register_menu_option("🧹 Limpiar Pistas (clean)", "clean", self.run_clean)
        self.register_menu_option("🔍 Auditoría (audit)", "audit", self.run_audit)
        self.register_menu_option("🩺 Diagnóstico (doctor)", "doctor", self.run_doctor)
        self.register_menu_option("⚙️ Configuración (config)", "config", self.run_config)
        self.register_menu_option("📖 Documentación (docs)", "docs", self.run_docs)


if __name__ == "__main__":
    check_and_install()
    app = MediaToolsApp()
    app.run()
