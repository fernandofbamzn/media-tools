"""
Entrypoint de Media Tools — hereda del framework clibaseapp.
main.py solo registra opciones de menú y delega a servicios.
"""

from pathlib import Path
from typing import Optional

import questionary
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from clibaseapp import (
    CLIBaseApp, BrowserMenu, BrowseResult, check_and_install,
    clear_screen, console, fmt, pause,
    show_header, show_info, show_success, show_warning, show_error,
)
from core.config import load_keep_languages, load_media_root
from models.schemas import ActionType
from services.media_service import MediaService, VIDEO_EXTENSIONS
from ui.components import render_audit_summary
from ui.clean_menu import ask_global_clean_plans


def _format_bytes(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:3.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


class MediaToolsApp(CLIBaseApp):
    """Aplicación CLI de gestión multimedia."""

    def __init__(self):
        super().__init__(app_name="media-tools", description="Media Tools CLI")

        self.config.default_config = {
            "media_root": str(Path.cwd().resolve()),
            "keep_languages": ["spa", "eng", "es", "en"],
        }

        self.require_binaries(["mkvmerge"])
        self._doctor_binaries.extend(["ffmpeg", "mediainfo"])
        self._doctor_paths = {"media_root": load_media_root()}
        self._app_dir = Path(__file__).parent.resolve()

        self.service = MediaService()

    def _browse(self) -> Optional[BrowseResult]:
        browser = BrowserMenu(file_extensions=VIDEO_EXTENSIONS, file_icon="🎬")
        result = browser.browse(load_media_root())
        if result:
            return BrowseResult(selected_path=result.selected_path, selection_type=result.selection_type)
        return None

    # ── Callbacks de negocio ──────────────────────────────────────

    def run_browse(self):
        from clibaseapp import render_browse_result
        render_browse_result(self._browse())

    def run_audit(self):
        render_audit_summary(self.service.audit(self._browse()))

    def run_clean(self):
        clear_screen()
        show_header("Limpiador de Pistas", "Inicio > Limpieza", icon="🧹")

        keep = load_keep_languages()
        extra = questionary.text(
            f"Idiomas a conservar: {', '.join(keep)}.\n¿Añadir para ESTA ejecución? (vacío = ninguno):",
        ).ask()

        if extra is None:
            return
        if extra.strip():
            keep = keep + [l.strip().lower() for l in extra.split(",") if l.strip()]

        selected = self._browse()
        if not selected:
            show_warning("Selección cancelada.")
            return

        plans = self.service.build_clean_plans(selected, keep)
        if not plans:
            show_warning("No se encontraron archivos multimedia para limpiar.")
            return

        try:
            final_plans = ask_global_clean_plans(plans)
        except KeyboardInterrupt:
            show_warning("\nPlanificación cancelada.")
            return

        clear_screen()
        show_header("Resumen del Plan", "Inicio > Limpieza > Resumen", icon="📝")
        plans_to_execute = []

        for p in final_plans:
            to_keep = sum(1 for a in p.track_actions if a.action == ActionType.KEEP)
            to_remove = sum(1 for a in p.track_actions if a.action == ActionType.REMOVE)
            show_info(f"🎬 {p.media_file.path.name}")
            console.print(f"   {fmt.tag(f'+ {to_keep} conservar', 'green')} | {fmt.tag(f'- {to_remove} eliminar', 'red')}\n")
            if to_remove > 0:
                plans_to_execute.append(p)

        if not plans_to_execute:
            show_success("Los archivos ya cumplen con la selección. Nada que borrar.")
            return

        total_remove = sum(sum(1 for a in p.track_actions if a.action == ActionType.REMOVE) for p in plans_to_execute)
        show_warning(f"ATENCIÓN: {total_remove} pistas en {len(plans_to_execute)} archivos serán eliminadas.")

        if not questionary.confirm("¿Aplicar cambios? (destructivo)").ask():
            show_warning("Cancelado.")
            return

        total_saved, errors = 0, 0
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
            BarColumn(), TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(), console=console,
        ) as progress:
            tid = progress.add_task("Limpiando...", total=len(plans_to_execute))
            for plan in plans_to_execute:
                progress.update(tid, description=f"Limpiando: {plan.media_file.path.name}...")
                try:
                    total_saved += self.service.execute_clean_plan(plan)
                except Exception as e:
                    errors += 1
                    show_error(f"{plan.media_file.path.name}: {e}")
                progress.advance(tid)

        clear_screen()
        show_header("✨ Limpieza Completada ✨", icon="🎉")
        msg = f"Procesados: {len(plans_to_execute) - errors}/{len(plans_to_execute)}\nEspacio: {_format_bytes(total_saved)}"
        show_success(msg) if errors == 0 else show_warning(f"{msg}\n{errors} errores.")

    # ── Registro ──────────────────────────────────────────────────

    def setup_commands(self) -> None:
        self.register_menu_option("🎬 Navegar Biblioteca", "browse", self.run_browse)
        self.register_menu_option("🧹 Limpiar Pistas", "clean", self.run_clean)
        self.register_menu_option("🔍 Auditoría", "audit", self.run_audit)


if __name__ == "__main__":
    check_and_install(["rich", "questionary", "typer"])
    MediaToolsApp().run()
