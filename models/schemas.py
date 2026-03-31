"""Modelos de datos especificos de media-tools."""

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
    track_name: str = ""
    title: str = ""
    language_ietf: str = ""
    channels: Optional[int] = None
    bitrate: Optional[int] = None
    default: bool = False
    forced: bool = False

    @property
    def label_name(self) -> str:
        return self.track_name or self.title or self.name


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
    """Resultado agregado de auditoria multimedia."""

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
    """Resultado de ejecucion de auditoria para la capa de presentacion."""

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
    """Accion planificada para una pista concreta."""

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


@dataclass(frozen=True)
class OptimizationProfile:
    """Perfil declarativo de optimizacion."""

    id: str
    title: str
    video_codec: str
    audio_codec: str
    ffmpeg_args: List[str]
    estimated_ratio: float
    description: str = ""
    tradeoffs: str = ""


@dataclass(frozen=True)
class OptimizationRecommendation:
    """Recomendacion estimada para un perfil de optimizacion."""

    profile: OptimizationProfile
    estimated_size: int
    estimated_savings: int
    estimated_ratio: float
    recommended: bool = False


@dataclass(frozen=True)
class OptimizationRecommendationSet:
    """Conjunto de recomendaciones basado en un archivo de referencia."""

    reference_file: MediaFile
    context: str
    options: List[OptimizationRecommendation] = field(default_factory=list)


@dataclass
class OptimizePlan:
    """Plan de optimizacion para un archivo."""

    media_file: MediaFile
    profile: OptimizationProfile
    output_path: Path
    original_size: int
    estimated_size: int
    can_optimize: bool
    skip_reason: str = ""


@dataclass
class OptimizeOutcome:
    """Resultado individual de una optimizacion."""

    input_path: Path
    output_path: Path
    original_size: int
    optimized_size: int
    bytes_saved: int


@dataclass
class OptimizeFailure:
    """Fallo durante la optimizacion."""

    file_path: Path
    message: str


@dataclass
class OptimizeResult:
    """Resultado agregado de optimizacion."""

    files_processed: int
    files_optimized: int
    files_skipped: int
    files_with_errors: int
    bytes_saved: int
    outputs: List[OptimizeOutcome] = field(default_factory=list)
    skipped: List[OptimizePlan] = field(default_factory=list)
    failures: List[OptimizeFailure] = field(default_factory=list)
