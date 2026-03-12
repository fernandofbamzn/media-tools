"""
Modelos de datos de la aplicación.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Track:
    """Representa una pista multimedia."""

    id: int
    codec: str
    language: str
    type: str
    name: str = ""
    channels: Optional[int] = None
    default: bool = False
    forced: bool = False


@dataclass
class MediaFile:
    """Representa un archivo multimedia analizado."""

    path: Path
    container: str
    tracks: List[Track] = field(default_factory=list)

    @property
    def audio_tracks(self) -> List[Track]:
        return [t for t in self.tracks if t.type == "audio"]

    @property
    def subtitle_tracks(self) -> List[Track]:
        return [t for t in self.tracks if t.type == "subtitles"]

    @property
    def video_tracks(self) -> List[Track]:
        return [t for t in self.tracks if t.type == "video"]


@dataclass
class BrowseResult:
    """Resultado de navegación del usuario."""

    selected_path: Path
    selection_type: str  # file | directory


@dataclass
class AuditReport:
    """Resultado agregado de auditoría."""

    total_files: int
    audio_languages: Dict[str, int]
    subtitle_languages: Dict[str, int]
    video_codecs: Dict[str, int]
    audio_codecs: Dict[str, int]
    files_without_subtitles: int
    files_without_spanish_audio: int
    files_with_duplicate_candidate_audio: int
