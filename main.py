"""
Entrypoint de Media Tools.

Este archivo contiene SOLO la definición del menú y la configuración
de la aplicación. Toda la lógica de negocio está en services/.
"""

from pathlib import Path

from clibaseapp import CLIBaseApp, check_and_install, render_browse_result
from core.config import load_media_root
from services.media_service import MediaService
from ui.components import render_audit_summary


class MediaToolsApp(CLIBaseApp):
    """Aplicación CLI de gestión multimedia.

    Hereda de CLIBaseApp, que proporciona automáticamente:
    Doctor, Configuración, Documentación, Actualizar y Salir.

    Esta clase solo registra las 3 opciones de negocio de media-tools:
    navegar, auditar y limpiar pistas multimedia.
    """

    def __init__(self):
        super().__init__(app_name="media-tools", description="Media Tools CLI")

        # Configuración por defecto específica de media-tools
        self.config.default_config = {
            "media_root": str(Path.cwd().resolve()),
            "keep_languages": ["spa", "eng", "es", "en"],
        }

        # Binarios requeridos y opcionales para el doctor
        self.require_binaries(["mkvmerge"])
        self._doctor_binaries.extend(["ffmpeg", "mediainfo"])
        self._doctor_paths = {"media_root": load_media_root()}

        # Directorio de la app (para doc_viewer)
        self._app_dir = Path(__file__).parent.resolve()

        # Servicio de negocio
        self.service = MediaService()

    # ── Callbacks del menú (delegación pura) ──────────────────────

    def _on_browse(self) -> None:
        """Navegar biblioteca multimedia."""
        render_browse_result(self.service.browse())

    def _on_audit(self) -> None:
        """Auditar archivos multimedia."""
        render_audit_summary(self.service.audit(self.service.browse()))

    def _on_clean(self) -> None:
        """Limpiar pistas de audio/subtítulos."""
        self.service.run_clean_workflow()

    # ── Registro de menú ──────────────────────────────────────────

    def setup_commands(self) -> None:
        """Registra las opciones de negocio en el menú interactivo."""
        self.register_menu_option("🎬 Navegar Biblioteca", "browse", self._on_browse)
        self.register_menu_option("🧹 Limpiar Pistas", "clean", self._on_clean)
        self.register_menu_option("🔍 Auditoría", "audit", self._on_audit)


if __name__ == "__main__":
    check_and_install(["rich", "questionary", "typer"])
    MediaToolsApp().run()
