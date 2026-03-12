"""
Modelos de datos específicos de media-tools.
Los modelos genéricos (BrowseResult, DoctorCheck, DoctorResult) vienen de clibaseapp.
"""

from dataclasses import dataclass, field
from enum import Enum
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
class AuditReport:
    """Resultado agregado de auditoría multimedia."""
    total_files: int
    audio_languages: Dict[str, int]
    subtitle_languages: Dict[str, int]
    video_codecs: Dict[str, int]
    audio_codecs: Dict[str, int]
    files_without_subtitles: int
    files_without_spanish_audio: int
    files_with_duplicate_candidate_audio: int
    detailed_files: List[MediaFile] = field(default_factory=list)


@dataclass
class AuditSummary:
    """Resultado de ejecución de auditoría para capa de presentación."""
    cancelled: bool
    selected_path: Optional[Path]
    selection_type: Optional[str]
    scanned_files: int
    report: Optional[AuditReport]


class ActionType(Enum):
    """Acciones a realizar sobre una pista."""
    KEEP = "keep"
    REMOVE = "remove"


@dataclass
class TrackAction:
    """Acción planificada para una pista concreta."""
    track: Track
    action: ActionType
    reason: str = ""


@dataclass
class CleanPlan:
    """Plan de limpieza proyectado para un archivo."""
    media_file: MediaFile
    track_actions: List[TrackAction]
    keep_languages: List[str]

    @property
    def tracks_to_keep(self) -> List[TrackAction]:
        return [t for t in self.track_actions if t.action == ActionType.KEEP]

    @property
    def tracks_to_remove(self) -> List[TrackAction]:
        return [t for t in self.track_actions if t.action == ActionType.REMOVE]
