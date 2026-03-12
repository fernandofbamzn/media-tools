"""
Servicio de negocio multimedia: auditoría y limpieza de pistas.
"""

import logging
from pathlib import Path
from typing import List, Optional

from clibaseapp import BrowseResult, scan_files
from data.repository import MediaRepository
from models.schemas import AuditSummary, CleanPlan
from services.audit_service import AuditService
from services.clean_service import CleanService

logger = logging.getLogger(__name__)

VIDEO_EXTENSIONS = {".mkv", ".mp4", ".m4v"}


class MediaService:
    """Servicio principal de lógica de negocio multimedia."""

    def __init__(self) -> None:
        self.repo = MediaRepository()
        self.audit_service = AuditService()
        self.clean_service = CleanService()

    def _resolve_files(self, result: BrowseResult) -> List[Path]:
        """Resuelve rutas: si es fichero, devuelve ese; si es directorio, escanea."""
        selected = result.selected_path
        if result.selection_type == "file":
            return [selected]
        return scan_files(selected, VIDEO_EXTENSIONS)

    def audit(self, result: Optional[BrowseResult]) -> AuditSummary:
        """Ejecuta auditoría sobre la selección."""
        if result is None:
            return AuditSummary(cancelled=True, selected_path=None, selection_type=None, scanned_files=0, report=None)

        files = self._resolve_files(result)
        if not files:
            return AuditSummary(cancelled=False, selected_path=result.selected_path, selection_type=result.selection_type, scanned_files=0, report=None)

        analyzed = self.repo.analyze_many(files)
        report = self.audit_service.build_report(analyzed)
        return AuditSummary(
            cancelled=False,
            selected_path=result.selected_path,
            selection_type=result.selection_type,
            scanned_files=len(files),
            report=report,
        )

    def build_clean_plans(self, result: Optional[BrowseResult], keep_languages: List[str]) -> List[CleanPlan]:
        """Genera planes de limpieza para cada archivo."""
        if result is None:
            return []

        files = self._resolve_files(result)
        if not files:
            return []

        analyzed = self.repo.analyze_many(files)
        return [self.clean_service.build_plan(mf, keep_languages) for mf in analyzed]

    def execute_clean_plan(self, plan: CleanPlan) -> int:
        """Ejecuta un plan y devuelve bytes ahorrados."""
        to_remove = [a for a in plan.track_actions if a.action.value == "remove"]
        if not to_remove:
            return 0

        initial_size = plan.media_file.path.stat().st_size
        self.repo.execute_remux(plan)
        final_size = plan.media_file.path.stat().st_size
        return max(0, initial_size - final_size)
