"""
Lógica de negocio principal.
"""

import logging
import shutil
from pathlib import Path
from typing import Optional

from data.repository import MediaRepository
from models.schemas import AuditSummary, BrowseResult, DoctorCheck, DoctorResult
from services.audit_service import AuditService
from services.browse_service import BrowseService

logger = logging.getLogger(__name__)


class MediaToolsService:
    """Servicio principal de la aplicación."""

    def __init__(self, default_root: Path) -> None:
        self.repo = MediaRepository()
        self.audit_service = AuditService()
        self.browse_service = BrowseService()
        self.default_root = default_root

    def doctor(self) -> DoctorResult:
        """Diagnóstico del sistema sin renderizado en consola."""
        try:
            checks = [
                DoctorCheck(name=binary, available=bool(shutil.which(binary)))
                for binary in ["mkvmerge", "ffmpeg", "mediainfo"]
            ]
            return DoctorResult(
                checks=checks,
                media_root=self.default_root,
                media_root_exists=self.default_root.exists(),
            )
        except Exception:
            logger.exception("Error ejecutando diagnóstico del sistema")
            raise

    def browse(self, result: Optional[BrowseResult]) -> Optional[BrowseResult]:
        """Valida y retorna la selección resuelta por la capa superior."""
        try:
            return result
        except Exception:
            logger.exception("Error procesando resultado de navegación")
            raise

    def audit(self, result: Optional[BrowseResult]) -> AuditSummary:
        """Ejecuta auditoría a partir de una selección ya resuelta."""
        try:
            if result is None:
                return AuditSummary(
                    cancelled=True,
                    selected_path=None,
                    selection_type=None,
                    scanned_files=0,
                    report=None,
                )

            selected = result.selected_path
            files = [selected] if result.selection_type == "file" else self.repo.scan(selected)

            if not files:
                return AuditSummary(
                    cancelled=False,
                    selected_path=selected,
                    selection_type=result.selection_type,
                    scanned_files=0,
                    report=None,
                )

            analyzed_files = self.repo.analyze_many(files)
            report = self.audit_service.build_report(analyzed_files)

            return AuditSummary(
                cancelled=False,
                selected_path=selected,
                selection_type=result.selection_type,
                scanned_files=len(files),
                report=report,
            )
        except Exception:
            logger.exception("Error ejecutando auditoría de biblioteca")
            raise
