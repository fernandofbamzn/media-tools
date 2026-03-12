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
from models.schemas import MediaFile, Track


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
