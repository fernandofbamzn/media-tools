"""
Repositorio de acceso al sistema de archivos y análisis multimedia.
"""

import json
import subprocess
from pathlib import Path
from typing import List

from models.schemas import MediaFile, Track


class MediaRepository:
    """Acceso a archivos multimedia."""

    VIDEO_EXTENSIONS = {".mkv", ".mp4", ".m4v"}

    def scan(self, root: Path) -> List[Path]:
        """Escanea recursivamente archivos multimedia."""
        files: List[Path] = []

        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in self.VIDEO_EXTENSIONS:
                files.append(path)

        return sorted(files)

    def analyze_file(self, path: Path) -> MediaFile:
        """Analiza un archivo con mkvmerge y devuelve sus pistas."""
        result = subprocess.run(
            ["mkvmerge", "-J", str(path)],
            capture_output=True,
            text=True,
            check=True,
        )

        data = json.loads(result.stdout)
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

        for file_path in files:
            analyzed.append(self.analyze_file(file_path))

        return analyzed
