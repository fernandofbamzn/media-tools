"""
Repositorio de acceso al sistema de archivos y análisis multimedia.
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import List

from core.exceptions import (
    BinaryMissingError,
    ExternalToolExecutionError,
    InvalidMediaMetadataError,
    MediaPermissionError,
)
from models.schemas import ActionType, CleanPlan, MediaFile, Track


logger = logging.getLogger(__name__)


class MediaRepository:
    """Acceso a archivos multimedia."""

    VIDEO_EXTENSIONS = {".mkv", ".mp4", ".m4v"}

    def scan(self, root: Path) -> List[Path]:
        """Escanea recursivamente archivos multimedia."""
        files: List[Path] = []

        try:
            for path in root.rglob("*"):
                if path.is_file() and path.suffix.lower() in self.VIDEO_EXTENSIONS:
                    files.append(path)
        except PermissionError as exc:
            logger.exception("Permiso denegado al escanear la ruta: %s", root)
            raise MediaPermissionError(
                f"Permiso denegado al escanear la ruta: {root}"
            ) from exc

        return sorted(files)

    def analyze_file(self, path: Path) -> MediaFile:
        """Analiza un archivo con mkvmerge y devuelve sus pistas."""
        try:
            result = subprocess.run(
                ["mkvmerge", "-J", str(path)],
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(result.stdout)
        except PermissionError as exc:
            logger.exception("Permiso denegado al analizar archivo: %s", path)
            raise MediaPermissionError(
                f"Permiso denegado al analizar el archivo: {path}"
            ) from exc
        except FileNotFoundError as exc:
            logger.exception("Binario mkvmerge no encontrado al analizar: %s", path)
            raise BinaryMissingError(
                "No se encontró 'mkvmerge'. Verifica dependencias del sistema."
            ) from exc
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            logger.error(
                "mkvmerge falló para %s con código %s: %s",
                path,
                exc.returncode,
                stderr,
            )
            raise ExternalToolExecutionError(
                f"mkvmerge devolvió código {exc.returncode} para '{path}'. {stderr}"
            ) from exc
        except json.JSONDecodeError as exc:
            logger.exception("JSON inválido devuelto por mkvmerge para: %s", path)
            raise InvalidMediaMetadataError(
                f"Salida JSON inválida de mkvmerge para '{path}'."
            ) from exc

        tracks: List[Track] = []

        for raw_track in data.get("tracks", []):
            props = raw_track.get("properties", {})

            tracks.append(
                Track(
                    id=int(raw_track["id"]),
                    codec=str(raw_track.get("codec", "")),
                    language=str(props.get("language", "und")),
                    type=str(raw_track.get("type", "")),
                    name=str(props.get("track_name", "")),
                    channels=props.get("audio_channels"),
                    default=bool(props.get("default_track", False)),
                    forced=bool(props.get("forced_track", False)),
                )
            )

        return MediaFile(
            path=path,
            container=str(data.get("container", {}).get("type", "unknown")),
            tracks=tracks,
        )

    def analyze_many(self, files: List[Path]) -> List[MediaFile]:
        """Analiza múltiples archivos multimedia."""
        analyzed: List[MediaFile] = []

        try:
            for file_path in files:
                analyzed.append(self.analyze_file(file_path))
        except (
            MediaPermissionError,
            BinaryMissingError,
            ExternalToolExecutionError,
            InvalidMediaMetadataError,
        ):
            raise
        except PermissionError as exc:
            logger.exception("Permiso denegado durante análisis en lote")
            raise MediaPermissionError(
                "Permiso denegado durante el análisis de archivos multimedia."
            ) from exc

        return analyzed

    def execute_remux(self, plan: CleanPlan) -> None:
        """Remuxea un archivo para eliminar las pistas marcadas para borrado."""
        input_path = plan.media_file.path
        temp_path = input_path.with_name(f"{input_path.stem}_tmp{input_path.suffix}")

        kept_audios = [a.track.id for a in plan.tracks_to_keep if a.track.type == "audio"]
        kept_subs = [a.track.id for a in plan.tracks_to_keep if a.track.type == "subtitles"]

        cmd = ["mkvmerge", "-o", str(temp_path)]

        if kept_audios:
            cmd.extend(["--audio-tracks", ",".join(map(str, kept_audios))])
        else:
            cmd.append("--no-audio")

        if kept_subs:
            cmd.extend(["--subtitle-tracks", ",".join(map(str, kept_subs))])
        else:
            cmd.append("--no-subtitles")

        cmd.append(str(input_path))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
        except FileNotFoundError as exc:
            logger.exception("Binario mkvmerge no encontrado al ejecutar limpieza: %s", input_path)
            raise BinaryMissingError("No se encontró 'mkvmerge'.") from exc
        except subprocess.CalledProcessError as exc:
            if temp_path.exists():
                temp_path.unlink()
            stderr = (exc.stderr or "").strip()
            stdout = (exc.stdout or "").strip()
            logger.error("Error al ejecutar mkvmerge: código %s\nStdout: %s\nStderr: %s", exc.returncode, stdout, stderr)
            raise ExternalToolExecutionError(f"Error al limpiar '{input_path.name}'. {stderr}") from exc

        # Si todo fue bien, reemplazar archivo original
        try:
            input_path.unlink()
            temp_path.rename(input_path)
        except OSError as exc:
            # Intentar limpiar temporal
            if temp_path.exists():
                temp_path.unlink()
            raise MediaPermissionError(f"Fallo de permisos al sobreescribir '{input_path.name}'.") from exc
