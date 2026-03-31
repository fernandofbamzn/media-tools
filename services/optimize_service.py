"""Servicio puro para planificar optimizaciones multimedia."""

from typing import Iterable, List, Optional

from models.schemas import (
    MediaFile,
    OptimizationProfile,
    OptimizationRecommendation,
    OptimizationRecommendationSet,
    OptimizePlan,
)

GIB = 1024 ** 3
SUPPORTED_OPTIMIZATION_SUFFIXES = {".mkv", ".mp4", ".m4v"}

CUSTOM_OPTIMIZATION_PROFILE = OptimizationProfile(
    id="custom-guided",
    title="Custom guiado",
    video_codec="custom",
    audio_codec="custom",
    ffmpeg_args=[],
    estimated_ratio=0.0,
    description="Analiza un archivo de la seleccion y propone compresiones estimadas.",
    tradeoffs="Aplica el mismo perfil final a todos los archivos de esta ejecucion.",
)

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
        description="HEVC por hardware para bajar tamano sin disparar el tiempo de proceso.",
        tradeoffs="Algo menos eficiente que x265 software y requiere soporte HEVC/VAAPI.",
    ),
    OptimizationProfile(
        id="h265-vaapi-compact",
        title="H.265 VAAPI Compacto (<10GB)",
        video_codec="hevc_vaapi",
        audio_codec="aac",
        ffmpeg_args=[
            "-vaapi_device", "/dev/dri/renderD128",
            "-vf", "format=nv12,hwupload",
            "-c:v", "hevc_vaapi",
            "-qp", "31",
            "-c:a", "aac",
            "-b:a", "192k",
            "-c:s", "copy",
            "-c:d", "copy",
            "-c:t", "copy",
        ],
        estimated_ratio=0.35,
        description="Aprieta la compresion por hardware para reducir tamano con mas agresividad.",
        tradeoffs="Mas perdida visible en escenas complejas y menor compatibilidad que H.264.",
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
        description="HEVC por CPU para priorizar ahorro frente a velocidad.",
        tradeoffs="Mucho mas lento que VAAPI y Opus puede dar problemas en algunos equipos.",
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
        description="Prioriza que el archivo siga reproduciendose en casi cualquier dispositivo.",
        tradeoffs="El ahorro suele ser claramente menor que con HEVC.",
    ),
]


class OptimizeService:
    """Construye planes de optimizacion conservadores."""

    def list_profiles(self) -> List[OptimizationProfile]:
        return [*DEFAULT_OPTIMIZATION_PROFILES, CUSTOM_OPTIMIZATION_PROFILE]

    def get_profile(self, profile_id: str) -> OptimizationProfile:
        for profile in self.list_profiles():
            if profile.id == profile_id:
                return profile
        raise ValueError(f"Perfil no soportado: {profile_id}")

    def build_custom_recommendations(
        self,
        media_files: Iterable[MediaFile],
    ) -> Optional[OptimizationRecommendationSet]:
        """Genera opciones guiadas de compresion basadas en un archivo de referencia."""
        media_files = list(media_files)
        reference_file = self._pick_reference_file(media_files)
        if reference_file is None:
            return None

        recommended_id = self._pick_recommended_profile_id(reference_file)
        options: List[OptimizationRecommendation] = []
        for profile in self._build_custom_profiles():
            plan = self.build_plan(reference_file, profile)
            if not plan.can_optimize:
                continue
            estimated_ratio = (
                plan.estimated_size / plan.original_size
                if plan.original_size
                else profile.estimated_ratio
            )
            options.append(
                OptimizationRecommendation(
                    profile=profile,
                    estimated_size=plan.estimated_size,
                    estimated_savings=max(0, plan.original_size - plan.estimated_size),
                    estimated_ratio=estimated_ratio,
                    recommended=profile.id == recommended_id,
                )
            )

        options.sort(key=lambda option: (not option.recommended, option.estimated_size))
        return OptimizationRecommendationSet(
            reference_file=reference_file,
            context=self._build_custom_context(reference_file, len(media_files)),
            options=options,
        )

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
        if suffix not in SUPPORTED_OPTIMIZATION_SUFFIXES:
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
        audio_tracks = media_file.audio_tracks

        ratio = profile.estimated_ratio
        if self._is_hevc_codec(video_codec):
            ratio += 0.15
        if profile.audio_codec == "libopus" and "opus" in audio_codecs:
            ratio += 0.05
        if any((track.channels or 0) > 2 for track in audio_tracks) and profile.audio_codec == "libopus":
            ratio += 0.03
        if media_file.path.exists() and media_file.path.stat().st_size < 2 * GIB:
            ratio += 0.04
        return min(max(ratio, 0.35), 0.95)

    def _pick_reference_file(self, media_files: Iterable[MediaFile]) -> Optional[MediaFile]:
        candidates = [
            media_file
            for media_file in media_files
            if len(media_file.video_tracks) == 1
            and media_file.path.suffix.lower() in SUPPORTED_OPTIMIZATION_SUFFIXES
        ]
        if not candidates:
            return None

        return max(
            candidates,
            key=lambda media_file: media_file.path.stat().st_size if media_file.path.exists() else 0,
        )

    def _build_custom_profiles(self) -> List[OptimizationProfile]:
        return [
            OptimizationProfile(
                id="custom-hevc-vaapi-quality",
                title="HEVC hardware suave",
                video_codec="hevc_vaapi",
                audio_codec="aac",
                ffmpeg_args=[
                    "-vaapi_device", "/dev/dri/renderD128",
                    "-vf", "format=nv12,hwupload",
                    "-c:v", "hevc_vaapi",
                    "-qp", "23",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-c:s", "copy",
                    "-c:d", "copy",
                    "-c:t", "copy",
                ],
                estimated_ratio=0.74,
                description="Mantiene la calidad cerca del original con una reduccion moderada.",
                tradeoffs="Ahorro medio. Requiere HEVC/VAAPI y no exprime al maximo la compresion.",
            ),
            OptimizationProfile(
                id="custom-hevc-vaapi-balanced",
                title="HEVC hardware equilibrado",
                video_codec="hevc_vaapi",
                audio_codec="aac",
                ffmpeg_args=[
                    "-vaapi_device", "/dev/dri/renderD128",
                    "-vf", "format=nv12,hwupload",
                    "-c:v", "hevc_vaapi",
                    "-qp", "27",
                    "-c:a", "aac",
                    "-b:a", "128k",
                    "-c:s", "copy",
                    "-c:d", "copy",
                    "-c:t", "copy",
                ],
                estimated_ratio=0.60,
                description="Buen punto medio entre espacio ganado, velocidad y perdida visual.",
                tradeoffs="Ligera perdida adicional frente al modo suave y menor compatibilidad que H.264.",
            ),
            OptimizationProfile(
                id="custom-hevc-x265-aggressive",
                title="HEVC software agresivo",
                video_codec="libx265",
                audio_codec="libopus",
                ffmpeg_args=[
                    "-c:v", "libx265",
                    "-preset", "slow",
                    "-crf", "29",
                    "-c:a", "libopus",
                    "-b:a", "80k",
                    "-c:s", "copy",
                    "-c:d", "copy",
                    "-c:t", "copy",
                ],
                estimated_ratio=0.46,
                description="Empuja la reduccion de tamano por encima del tiempo de proceso.",
                tradeoffs="Es la opcion mas lenta y la que mas degrada calidad y compatibilidad.",
            ),
            OptimizationProfile(
                id="custom-h264-aac-compatible",
                title="H.264 alta compatibilidad",
                video_codec="libx264",
                audio_codec="aac",
                ffmpeg_args=[
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-crf", "22",
                    "-c:a", "aac",
                    "-b:a", "128k",
                    "-c:s", "copy",
                    "-c:d", "copy",
                    "-c:t", "copy",
                ],
                estimated_ratio=0.82,
                description="Recorta tamano manteniendo la mejor compatibilidad posible.",
                tradeoffs="Reduce bastante menos que las opciones HEVC.",
            ),
        ]

    def _pick_recommended_profile_id(self, media_file: MediaFile) -> str:
        video_codec = (media_file.video_tracks[0].codec or "").lower() if media_file.video_tracks else ""
        original_size = media_file.path.stat().st_size if media_file.path.exists() else 0

        if self._is_hevc_codec(video_codec):
            return "custom-hevc-vaapi-quality"
        if original_size >= 12 * GIB:
            return "custom-hevc-x265-aggressive"
        if original_size >= 4 * GIB:
            return "custom-hevc-vaapi-balanced"
        return "custom-hevc-vaapi-quality"

    def _build_custom_context(self, media_file: MediaFile, selection_size: int) -> str:
        original_size = media_file.path.stat().st_size if media_file.path.exists() else 0
        video_codec = (
            media_file.video_tracks[0].codec or "desconocido"
            if media_file.video_tracks
            else "desconocido"
        )
        prefix = (
            "Referencia tomada del archivo mas grande de la seleccion"
            if selection_size > 1
            else "Referencia tomada del archivo seleccionado"
        )
        note = (
            "Ya viene en HEVC; el margen de ahorro extra suele ser mas limitado."
            if self._is_hevc_codec(video_codec.lower())
            else "Al venir en un codec mas antiguo, HEVC deberia aportar un recorte apreciable."
        )
        return f"{prefix}: {media_file.path.name} ({self._format_bytes(original_size)}, {video_codec}). {note}"

    def _format_bytes(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:3.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def _is_hevc_codec(self, codec: str) -> bool:
        return "hevc" in codec or "265" in codec
