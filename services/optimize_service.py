"""Servicio puro para planificar optimizaciones multimedia."""

from pathlib import Path
from typing import Iterable, List

from models.schemas import MediaFile, OptimizationProfile, OptimizePlan

DEFAULT_OPTIMIZATION_PROFILES = [
    OptimizationProfile(
        id="h265-vaapi",
        title="H.265 VAAPI (Hardware Intel)",
        video_codec="hevc_vaapi",
        audio_codec="libopus",
        ffmpeg_args=[
            "-vaapi_device", "/dev/dri/renderD128",
            "-vf", "format=nv12,hwupload",
            "-c:v", "hevc_vaapi",
            "-qp", "25",
            "-c:a", "libopus",
            "-b:a", "96k",
            "-c:s", "copy",
            "-c:d", "copy",
            "-c:t", "copy",
        ],
        estimated_ratio=0.70,
    ),
    OptimizationProfile(
        id="h265-opus",
        title="H.265/Opus ahorro",
        video_codec="libx265",
        audio_codec="libopus",
        ffmpeg_args=[
            "-c:v",
            "libx265",
            "-preset",
            "medium",
            "-crf",
            "28",
            "-c:a",
            "libopus",
            "-b:a",
            "96k",
            "-c:s",
            "copy",
            "-c:d",
            "copy",
            "-c:t",
            "copy",
        ],
        estimated_ratio=0.62,
    ),
    OptimizationProfile(
        id="h264-aac",
        title="H.264/AAC compatibilidad",
        video_codec="libx264",
        audio_codec="aac",
        ffmpeg_args=[
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-c:s",
            "copy",
            "-c:d",
            "copy",
            "-c:t",
            "copy",
        ],
        estimated_ratio=0.78,
    ),
]


class OptimizeService:
    """Construye planes de optimizacion conservadores."""

    def list_profiles(self) -> List[OptimizationProfile]:
        return list(DEFAULT_OPTIMIZATION_PROFILES)

    def get_profile(self, profile_id: str) -> OptimizationProfile:
        for profile in DEFAULT_OPTIMIZATION_PROFILES:
            if profile.id == profile_id:
                return profile
        raise ValueError(f"Perfil no soportado: {profile_id}")

    def build_plan(self, media_file: MediaFile, profile: OptimizationProfile) -> OptimizePlan:
        original_size = media_file.path.stat().st_size if media_file.path.exists() else 0
        output_path = media_file.path.with_suffix(".optimized.mkv")

        if len(media_file.video_tracks) != 1:
            return OptimizePlan(
                media_file=media_file,
                profile=profile,
                output_path=output_path,
                original_size=original_size,
                estimated_size=original_size,
                can_optimize=False,
                skip_reason="Se requiere exactamente una pista de video.",
            )

        suffix = media_file.path.suffix.lower()
        if suffix not in {".mkv", ".mp4", ".m4v"}:
            return OptimizePlan(
                media_file=media_file,
                profile=profile,
                output_path=output_path,
                original_size=original_size,
                estimated_size=original_size,
                can_optimize=False,
                skip_reason="Contenedor no soportado para optimizacion.",
            )

        estimated_size = int(original_size * self._estimate_ratio(media_file, profile))
        return OptimizePlan(
            media_file=media_file,
            profile=profile,
            output_path=output_path,
            original_size=original_size,
            estimated_size=estimated_size,
            can_optimize=True,
        )

    def build_plans(
        self,
        media_files: Iterable[MediaFile],
        profile: OptimizationProfile,
    ) -> List[OptimizePlan]:
        return [self.build_plan(media_file, profile) for media_file in media_files]

    def _estimate_ratio(self, media_file: MediaFile, profile: OptimizationProfile) -> float:
        video_codec = (media_file.video_tracks[0].codec or "").lower() if media_file.video_tracks else ""
        audio_codecs = {(track.codec or "").lower() for track in media_file.audio_tracks}

        ratio = profile.estimated_ratio
        if "hevc" in video_codec or "265" in video_codec:
            ratio += 0.15
        if profile.audio_codec == "libopus" and "opus" in audio_codecs:
            ratio += 0.05
        return min(max(ratio, 0.35), 0.95)
