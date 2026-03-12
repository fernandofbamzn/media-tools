"""
Lógica de negocio principal.
"""

import shutil
from pathlib import Path

from data.repository import MediaRepository
from services.audit_service import AuditService
from services.browse_service import BrowseService
from ui.components import (
    console,
    dict_table,
    show_error,
    show_header,
    show_info,
    show_success,
    show_warning,
)


class MediaToolsService:
    """Servicio principal de la aplicación."""

    def __init__(self) -> None:
        self.repo = MediaRepository()
        self.audit_service = AuditService()
        self.browse_service = BrowseService()
        self.default_root = Path("/mnt/Filmoteca")

    def doctor(self) -> None:
        """Diagnóstico del sistema."""
        show_header("Media Tools Doctor", "Inicio > Doctor")

        for binary in ["mkvmerge", "ffmpeg", "mediainfo"]:
            if shutil.which(binary):
                show_success(f"{binary} encontrado")
            else:
                show_error(f"{binary} NO encontrado")

        if self.default_root.exists():
            show_success(f"Raíz multimedia accesible: {self.default_root}")
        else:
            show_warning(f"No existe la raíz multimedia: {self.default_root}")

    def browse(self) -> None:
        """Navegación interactiva por la biblioteca."""
        show_header("Navegador de Biblioteca", "Inicio > Navegación")

        result = self.browse_service.browse(self.default_root)

        if result is None:
            show_warning("Navegación cancelada.")
            return

        show_success(f"Seleccionado: {result.selected_path}")
        show_info(f"Tipo de selección: {result.selection_type}")

    def audit(self) -> None:
        """Auditoría de biblioteca con selección interactiva."""
        show_header("Auditoría de Biblioteca", "Inicio > Auditoría")

        result = self.browse_service.browse(self.default_root)

        if result is None:
            show_warning("Auditoría cancelada.")
            return

        selected = result.selected_path

        if result.selection_type == "file":
            files = [selected]
        else:
            files = self.repo.scan(selected)

        if not files:
            show_warning("No se encontraron archivos multimedia.")
            return

        show_info(f"Analizando {len(files)} archivos...")
        analyzed_files = self.repo.analyze_many(files)
        report = self.audit_service.build_report(analyzed_files)

        show_success(f"Archivos analizados: {report.total_files}")
        console.print(
            dict_table("Idiomas de audio", report.audio_languages, "Idioma", "Pistas")
        )
        console.print(
            dict_table("Idiomas de subtítulos", report.subtitle_languages, "Idioma", "Pistas")
        )
        console.print(
            dict_table("Códecs de vídeo", report.video_codecs, "Códec", "Pistas")
        )
        console.print(
            dict_table("Códecs de audio", report.audio_codecs, "Códec", "Pistas")
        )

        show_info(f"Archivos sin subtítulos: {report.files_without_subtitles}")
        show_info(f"Archivos sin audio en español: {report.files_without_spanish_audio}")
        show_info(
            f"Archivos con posible audio duplicado: {report.files_with_duplicate_candidate_audio}"
        )
