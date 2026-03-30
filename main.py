import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

"""Entrypoint de Media Tools."""
os.environ["LIBVA_DRIVER_NAME"] = "iHD"

def _bootstrap() -> None:
    if os.getenv("CLIBASEAPP_SKIP_BOOTSTRAP") == "1":
        return

    app_dir = Path(__file__).parent.resolve()
    try:
        from clibaseapp.core.bootstrap import ensure_venv
    except ImportError as exc:
        venv_dir = app_dir / ".venv"
        venv_python = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        if not venv_dir.exists():
            subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
        subprocess.run([str(venv_python), "-m", "pip", "install", "-r", str(app_dir / "requirements.txt")], check=True)
        os.execv(str(venv_python), [str(venv_python)] + sys.argv)
        raise SystemExit(1) from exc

    ensure_venv(app_dir=app_dir)


_bootstrap()

try:
    from clibaseapp import CLIBaseApp, MenuAction
except ImportError:
    from clibaseapp import CLIBaseApp

    @dataclass
    class MenuAction:
        id: str
        title: str
        handler: object
        order: int = 100
        visible: object = None
        enabled: object = None
        status_suffix: object = None
from core.config import DEFAULT_KEEP_LANGUAGES, load_media_root
from services.media_service import MediaService
from ui.workflows import run_clean_workflow, run_optimize_workflow


class MediaToolsApp(CLIBaseApp):
    """Aplicacion CLI de gestion multimedia."""

    def __init__(self) -> None:
        super().__init__(app_name="media-tools", description="Media Tools CLI")

        self.config.default_config = {
            "media_root": str(Path.cwd().resolve()),
            "keep_languages": DEFAULT_KEEP_LANGUAGES.copy(),
        }

        self.require_binaries(["mkvmerge"])
        self._doctor_binaries.extend(["ffmpeg", "ffprobe", "mediainfo"])
        self.service = MediaService()

    def _media_root_status(self) -> str:
        path = load_media_root(self.config)
        return f"[{path}]"

    def _on_clean(self) -> None:
        run_clean_workflow(self.service, self.config)

    def _on_optimize(self) -> None:
        run_optimize_workflow(self.service, self.config)

    def _register_action_compat(self, action: MenuAction) -> None:
        register_menu_action = getattr(self, "register_menu_action", None)
        if callable(register_menu_action):
            register_menu_action(action)
            return
        self.register_menu_option(action.title, action.id, action.handler)

    def setup_commands(self) -> None:
        self._doctor_paths = {"media_root": load_media_root(self.config)}
        self._register_action_compat(
            MenuAction(
                id="clean",
                title="🧹 Limpieza de Pistas",
                handler=self._on_clean,
                order=100,
                status_suffix=self._media_root_status,
            )
        )
        self._register_action_compat(
            MenuAction(
                id="optimize",
                title="⚙️ Optimizacion de Tamano",
                handler=self._on_optimize,
                order=110,
                status_suffix=self._media_root_status,
            )
        )


if __name__ == "__main__":
    MediaToolsApp().run()
