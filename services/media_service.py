"""
Servicio orquestador de negocio multimedia.

Responsabilidad: coordinar el flujo entre el repositorio de datos
(MediaRepository), los servicios de auditoría (AuditService) y limpieza
(CleanService), y la capa de UI para completar operaciones de extremo
a extremo.

Funciones principales:
  - Auditoría: escanea archivos → analiza metadatos → genera informe.
  - Limpieza: escanea → analiza → genera planes → ejecuta remux.
  - Navegación: resuelve selección de archivos/directorios.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import questionary
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from clibaseapp import (
    BrowserMenu, BrowseResult, scan_files,
    clear_screen, console, fmt,
    show_header, show_info, show_success, show_warning, show_error,
)
from core.config import load_keep_languages, load_media_root
from data.repository import MediaRepository
from models.schemas import ActionType, AuditSummary, CleanPlan
from services.audit_service import AuditService
from services.clean_service import CleanService
from ui.clean_menu import ask_global_clean_plans

logger = logging.getLogger(__name__)

VIDEO_EXTENSIONS = {".mkv", ".mp4", ".m4v"}
"""Extensiones de archivo multimedia soportadas por la aplicación."""


def _format_bytes(size: int) -> str:
    """Formatea un tamaño en bytes a unidad legible (KB, MB, GB, etc)."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:3.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


@dataclass
class CleanResult:
    """Resultado de una ejecución de limpieza."""
    files_processed: int
    files_with_errors: int
    bytes_saved: int


class MediaService:
    """Servicio principal que orquesta toda la lógica de negocio multimedia.

    Coordina:
      - MediaRepository: acceso a archivos y ejecución de mkvmerge.
      - AuditService: generación de informes estadísticos.
      - CleanService: planificación de limpieza de pistas.

    No contiene lógica de UI directa — recibe y devuelve datos puros.
    La capa de presentación (components.py) se encarga de renderizar.
    """

    def __init__(self) -> None:
        self.repo = MediaRepository()
        self.audit_service = AuditService()
        self.clean_service = CleanService()

    # ── Helpers internos ──────────────────────────────────────────

    def _resolve_files(self, result: BrowseResult) -> List[Path]:
        """Resuelve la selección del usuario a una lista de archivos.

        Si el usuario seleccionó un archivo, devuelve solo ese.
        Si seleccionó un directorio, escanea recursivamente por extensiones.

        Args:
            result: Resultado de navegación del usuario.

        Returns:
            Lista ordenada de Paths de archivos multimedia encontrados.
        """
        if result.selection_type == "file":
            return [result.selected_path]
        return scan_files(result.selected_path, VIDEO_EXTENSIONS)

    def browse(self) -> Optional[BrowseResult]:
        """Abre el navegador interactivo de archivos multimedia.

        Returns:
            BrowseResult con la selección del usuario, o None si canceló.
        """
        browser = BrowserMenu(file_extensions=VIDEO_EXTENSIONS, file_icon="🎬")
        result = browser.browse(load_media_root())
        if result:
            return BrowseResult(
                selected_path=result.selected_path,
                selection_type=result.selection_type,
            )
        return None

    # ── Operaciones de negocio ────────────────────────────────────

    def audit(self, result: Optional[BrowseResult]) -> AuditSummary:
        """Ejecuta una auditoría completa sobre la selección del usuario.

        Args:
            result: Selección de archivo/directorio, o None si se canceló.

        Returns:
            AuditSummary con el informe o estado de cancelación.
        """
        if result is None:
            return AuditSummary(
                cancelled=True, selected_path=None,
                selection_type=None, scanned_files=0, report=None,
            )

        files = self._resolve_files(result)
        if not files:
            return AuditSummary(
                cancelled=False, selected_path=result.selected_path,
                selection_type=result.selection_type, scanned_files=0, report=None,
            )

        analyzed = self.repo.analyze_many(files)
        report = self.audit_service.build_report(analyzed)
        return AuditSummary(
            cancelled=False, selected_path=result.selected_path,
            selection_type=result.selection_type,
            scanned_files=len(files), report=report,
        )

    def build_clean_plans(self, result: BrowseResult, keep_languages: List[str]) -> List[CleanPlan]:
        """Genera un plan de limpieza para cada archivo seleccionado.

        Args:
            result: Selección de archivo/directorio del usuario.
            keep_languages: Códigos de idioma a conservar (ej: ["spa", "eng"]).

        Returns:
            Lista de CleanPlan, uno por cada archivo multimedia encontrado.
        """
        files = self._resolve_files(result)
        if not files:
            return []

        analyzed = self.repo.analyze_many(files)
        return [self.clean_service.build_plan(mf, keep_languages) for mf in analyzed]

    def execute_clean_plan(self, plan: CleanPlan) -> int:
        """Ejecuta un plan de limpieza individual sobre un archivo.

        Calcula el tamaño antes y después del remux para informar del
        espacio recuperado.

        Args:
            plan: Plan de limpieza con las acciones a ejecutar.

        Returns:
            Bytes ahorrados (diferencia de tamaño antes/después).
        """
        to_remove = [a for a in plan.track_actions if a.action == ActionType.REMOVE]
        if not to_remove:
            return 0

        initial_size = plan.media_file.path.stat().st_size
        self.repo.execute_remux(plan)
        final_size = plan.media_file.path.stat().st_size
        return max(0, initial_size - final_size)

    # ── Workflows completos (UI + negocio) ────────────────────────

    def run_clean_workflow(self) -> None:
        """Ejecuta el flujo completo de limpieza de pistas.

        Pasos:
          1. Preguntar idiomas adicionales a conservar.
          2. Navegar y seleccionar archivos/directorio.
          3. Generar planes de limpieza por archivo.
          4. Mostrar checklist para revisión del usuario.
          5. Mostrar resumen con conteos de pistas a borrar.
          6. Pedir confirmación destructiva.
          7. Ejecutar remux con barra de progreso.
          8. Mostrar informe final con espacio recuperado.
        """
        clear_screen()
        show_header("Limpiador de Pistas", "Inicio > Limpieza", icon="🧹")

        # 1. Idiomas a conservar
        keep = load_keep_languages()
        extra = questionary.text(
            f"Idiomas a conservar: {', '.join(keep)}.\n"
            "¿Añadir para ESTA ejecución? (vacío = ninguno):",
        ).ask()

        if extra is None:
            return
        if extra.strip():
            keep = keep + [l.strip().lower() for l in extra.split(",") if l.strip()]

        # 2. Selección de archivos
        selected = self.browse()
        if not selected:
            show_warning("Selección cancelada.")
            return

        # 3. Generar planes
        plans = self.build_clean_plans(selected, keep)
        if not plans:
            show_warning("No se encontraron archivos multimedia para limpiar.")
            return

        # 4. Checklist interactivo
        try:
            final_plans = ask_global_clean_plans(plans)
        except KeyboardInterrupt:
            show_warning("\nPlanificación cancelada.")
            return

        # 5. Resumen
        clear_screen()
        show_header("Resumen del Plan", "Inicio > Limpieza > Resumen", icon="📝")
        plans_to_execute = []

        for p in final_plans:
            to_keep = sum(1 for a in p.track_actions if a.action == ActionType.KEEP)
            to_remove = sum(1 for a in p.track_actions if a.action == ActionType.REMOVE)
            show_info(f"🎬 {p.media_file.path.name}")
            console.print(
                f"   {fmt.tag(f'+ {to_keep} conservar', 'green')} | "
                f"{fmt.tag(f'- {to_remove} eliminar', 'red')}\n"
            )
            if to_remove > 0:
                plans_to_execute.append(p)

        if not plans_to_execute:
            show_success("Los archivos ya cumplen con la selección. Nada que borrar.")
            return

        # 6. Confirmación destructiva
        total_remove = sum(
            sum(1 for a in p.track_actions if a.action == ActionType.REMOVE)
            for p in plans_to_execute
        )
        show_warning(f"ATENCIÓN: {total_remove} pistas en {len(plans_to_execute)} archivos serán eliminadas.")

        if not questionary.confirm("¿Aplicar cambios? (destructivo)").ask():
            show_warning("Cancelado.")
            return

        # 7. Ejecución con progreso
        result = self._execute_plans_with_progress(plans_to_execute)

        # 8. Informe final
        clear_screen()
        show_header("✨ Limpieza Completada ✨", icon="🎉")
        msg = (
            f"Procesados: {result.files_processed - result.files_with_errors}"
            f"/{result.files_processed}\n"
            f"Espacio: {_format_bytes(result.bytes_saved)}"
        )
        if result.files_with_errors == 0:
            show_success(msg)
        else:
            show_warning(f"{msg}\n{result.files_with_errors} errores.")

    def _execute_plans_with_progress(self, plans: List[CleanPlan]) -> CleanResult:
        """Ejecuta una lista de planes de limpieza con barra de progreso.

        Args:
            plans: Lista de CleanPlan a ejecutar.

        Returns:
            CleanResult con estadísticas de la ejecución.
        """
        total_saved, errors = 0, 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            tid = progress.add_task("Limpiando...", total=len(plans))
            for plan in plans:
                progress.update(tid, description=f"Limpiando: {plan.media_file.path.name}...")
                try:
                    total_saved += self.execute_clean_plan(plan)
                except Exception as e:
                    errors += 1
                    show_error(f"{plan.media_file.path.name}: {e}")
                progress.advance(tid)

        return CleanResult(
            files_processed=len(plans),
            files_with_errors=errors,
            bytes_saved=total_saved,
        )
