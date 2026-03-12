"""
Repositorio de acceso a archivos multimedia y análisis con mkvmerge.
El escaneo genérico de archivos se delega a clibaseapp.core.scanner.
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import List

from clibaseapp.exceptions import BinaryMissingError, ExternalToolError, PermissionAccessError
from core.exceptions import InvalidMediaMetadataError
from models.schemas import CleanPlan, MediaFile, Track


logger = logging.getLogger(__name__)


class MediaRepository:
    """Acceso a archivos multimedia (análisis y remux)."""

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
            raise PermissionAccessError(f"Permiso denegado al analizar: {path}") from exc
        except FileNotFoundError as exc:
            logger.exception("Binario mkvmerge no encontrado")
            raise BinaryMissingError("No se encontró 'mkvmerge'.") from exc
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            logger.error("mkvmerge falló para %s: %s", path, stderr)
            raise ExternalToolError(f"mkvmerge error para '{path.name}'. {stderr}") from exc
        except json.JSONDecodeError as exc:
            logger.exception("JSON inválido de mkvmerge para: %s", path)
            raise InvalidMediaMetadataError(f"JSON inválido de mkvmerge para '{path}'.") from exc

        tracks: List[Track] = []
        for raw_track in data.get("tracks", []):
            props = raw_track.get("properties", {})
            tracks.append(Track(
                id=int(raw_track["id"]),
                codec=str(raw_track.get("codec", "")),
                language=str(props.get("language", "und")),
                type=str(raw_track.get("type", "")),
                name=str(props.get("track_name", "")),
                channels=props.get("audio_channels"),
                default=bool(props.get("default_track", False)),
                forced=bool(props.get("forced_track", False)),
            ))

        return MediaFile(
            path=path,
            container=str(data.get("container", {}).get("type", "unknown")),
            tracks=tracks,
        )

    def analyze_many(self, files: List[Path]) -> List[MediaFile]:
        """Analiza múltiples archivos multimedia."""
        return [self.analyze_file(f) for f in files]

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
            subprocess.run(cmd, capture_output=True, text=True, check=True)
        except FileNotFoundError as exc:
            raise BinaryMissingError("No se encontró 'mkvmerge'.") from exc
        except subprocess.CalledProcessError as exc:
            if temp_path.exists():
                temp_path.unlink()
            stderr = (exc.stderr or "").strip()
            raise ExternalToolError(f"Error al limpiar '{input_path.name}'. {stderr}") from exc

        try:
            input_path.unlink()
            temp_path.rename(input_path)
        except OSError as exc:
            if temp_path.exists():
                temp_path.unlink()
            raise PermissionAccessError(f"Fallo de permisos al sobreescribir '{input_path.name}'.") from exc
