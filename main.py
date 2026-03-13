"""
Entrypoint de Media Tools.

Este archivo contiene SOLO la definición del menú y la configuración
de la aplicación. La lógica de negocio está en services/ y los
workflows interactivos en ui/.

Al arrancar, verifica que clibaseapp y el resto de dependencias estén
instaladas antes de importarlas.
"""

import importlib
import importlib.util
import subprocess
import sys


def _ensure_dependencies() -> None:
    """Verifica que las dependencias críticas estén instaladas.

    Si falta clibaseapp u otra dependencia, ejecuta pip install -r requirements.txt
    automáticamente. Esto permite que un git pull en producción funcione sin pasos
    manuales adicionales.
    """
    required = ["clibaseapp", "rich", "questionary", "typer"]
    missing = [pkg for pkg in required if importlib.util.find_spec(pkg) is None]

    if not missing:
        return

    print(f"\n⚠ Dependencias faltantes: {', '.join(missing)}")
    print("  Instalando automáticamente desde requirements.txt...\n")

    try:
        from pathlib import Path
        req_file = Path(__file__).parent / "requirements.txt"
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
            check=True,
        )
        print("\n✔ Dependencias instaladas. Reiniciando...\n")
        import os
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as exc:
        print(f"\n✖ Error al instalar dependencias: {exc}")
        print("  Ejecuta manualmente: pip install -r requirements.txt")
        sys.exit(1)


# Bootstrap: verificar ANTES de importar clibaseapp
_ensure_dependencies()

# ── Imports seguros (clibaseapp ya está instalado) ────────────────
from pathlib import Path

from clibaseapp import CLIBaseApp, render_browse_result
from core.config import DEFAULT_KEEP_LANGUAGES, load_media_root
from services.media_service import MediaService
from ui.components import render_audit_summary
from ui.workflows import browse_media, run_clean_workflow


class MediaToolsApp(CLIBaseApp):
    """Aplicación CLI de gestión multimedia.

    Hereda de CLIBaseApp, que proporciona automáticamente:
    Doctor, Configuración, Documentación, Actualizar y Salir.

    Esta clase solo registra las 3 opciones de negocio de media-tools:
    navegar, auditar y limpiar pistas multimedia.
    """

    def __init__(self) -> None:
        super().__init__(app_name="media-tools", description="Media Tools CLI")

        # Configuración por defecto específica de media-tools
        self.config.default_config = {
            "media_root": str(Path.cwd().resolve()),
            "keep_languages": DEFAULT_KEEP_LANGUAGES.copy(),
        }

        # Binarios requeridos y opcionales para el doctor
        self.require_binaries(["mkvmerge"])
        self._doctor_binaries.extend(["ffmpeg", "mediainfo"])
        self._doctor_paths = {"media_root": load_media_root(self.config)}

        # Directorio de la app (para doc_viewer)
        self._app_dir = Path(__file__).parent.resolve()

        # Servicio de negocio
        self.service = MediaService()

    # ── Callbacks del menú (delegación pura) ──────────────────────

    def _on_browse(self) -> None:
        """Navegar biblioteca multimedia."""
        render_browse_result(browse_media(self.config))

    def _on_audit(self) -> None:
        """Auditar archivos multimedia."""
        render_audit_summary(self.service.audit(browse_media(self.config)))

    def _on_clean(self) -> None:
        """Limpiar pistas de audio/subtítulos."""
        run_clean_workflow(self.service, self.config)

    # ── Registro de menú ──────────────────────────────────────────

    def setup_commands(self) -> None:
        """Registra las opciones de negocio en el menú interactivo."""
        self.register_menu_option("🎬 Navegar Biblioteca", "browse", self._on_browse)
        self.register_menu_option("🧹 Limpiar Pistas", "clean", self._on_clean)
        self.register_menu_option("🔍 Auditoría", "audit", self._on_audit)


if __name__ == "__main__":
    MediaToolsApp().run()
