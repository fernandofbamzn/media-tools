"""
Servicio orquestador de negocio multimedia.

Responsabilidad: coordinar el flujo entre el repositorio de datos
(MediaRepository), los servicios de auditoría (AuditService) y limpieza
(CleanService), sin depender de la capa de interfaz.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from clibaseapp import BrowseResult, scan_files
from data.repository import MediaRepository
from models.schemas import ActionType, AuditSummary, CleanPlan
from services.audit_service import AuditService
from services.clean_service import CleanService

VIDEO_EXTENSIONS = {".mkv", ".mp4", ".m4v"}
"""Extensiones de archivo multimedia soportadas por la aplicación."""


@dataclass
class CleanFailure:
    """Error producido al ejecutar la limpieza de un archivo."""

    file_path: Path
    message: str


@dataclass
class CleanResult:
    """Resultado agregado de una ejecución de limpieza."""

    files_processed: int
    files_with_errors: int
    bytes_saved: int
    failures: List[CleanFailure] = field(default_factory=list)


class MediaService:
    """Servicio principal que orquesta toda la lógica de negocio multimedia.

    La clase solo recibe datos de entrada, coordina repositorio y servicios
    especializados, y devuelve modelos puros listos para que la UI los renderice.
    """

    def __init__(self) -> None:
        self.repo = MediaRepository()
        self.audit_service = AuditService()
        self.clean_service = CleanService()

    def _resolve_files(self, result: BrowseResult) -> List[Path]:
        """Resuelve una selección de archivo/directorio a archivos multimedia.

        Si la selección ya es un fichero, evita escaneos innecesarios.
        """

        if result.selection_type == "file":
            return [result.selected_path]
        return scan_files(result.selected_path, VIDEO_EXTENSIONS)

    def audit(self, result: Optional[BrowseResult]) -> AuditSummary:
        """Ejecuta una auditoría completa sobre la selección del usuario."""

        if result is None:
            return AuditSummary(
                cancelled=True,
                selected_path=None,
                selection_type=None,
                scanned_files=0,
                report=None,
            )

        files = self._resolve_files(result)
        if not files:
            return AuditSummary(
                cancelled=False,
                selected_path=result.selected_path,
                selection_type=result.selection_type,
                scanned_files=0,
                report=None,
            )

        analyzed = self.repo.analyze_many(files)
        report = self.audit_service.build_report(analyzed)
        return AuditSummary(
            cancelled=False,
            selected_path=result.selected_path,
            selection_type=result.selection_type,
            scanned_files=len(files),
            report=report,
        )

    def build_clean_plans(self, result: BrowseResult, keep_languages: List[str]) -> List[CleanPlan]:
        """Genera un plan de limpieza para cada archivo seleccionado."""

        files = self._resolve_files(result)
        if not files:
            return []

        analyzed = self.repo.analyze_many(files)
        return [self.clean_service.build_plan(media_file, keep_languages) for media_file in analyzed]

    def execute_clean_plan(self, plan: CleanPlan) -> int:
        """Ejecuta un plan individual y devuelve los bytes ahorrados."""

        to_remove = [action for action in plan.track_actions if action.action == ActionType.REMOVE]
        if not to_remove:
            return 0

        initial_size = plan.media_file.path.stat().st_size
        self.repo.execute_remux(plan)
        final_size = plan.media_file.path.stat().st_size
        return max(0, initial_size - final_size)

    def execute_clean_plans(self, plans: List[CleanPlan]) -> CleanResult:
        """Ejecuta múltiples planes y devuelve un resultado puro.

        El método agrega errores por archivo sin emitir salida por consola,
        para que la capa de UI decida cómo mostrar cada incidencia.
        """

        total_saved = 0
        failures: List[CleanFailure] = []

        for plan in plans:
            try:
                total_saved += self.execute_clean_plan(plan)
            except Exception as exc:
                failures.append(CleanFailure(file_path=plan.media_file.path, message=str(exc)))

        return CleanResult(
            files_processed=len(plans),
            files_with_errors=len(failures),
            bytes_saved=total_saved,
            failures=failures,
        )
