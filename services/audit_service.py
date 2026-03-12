"""
Servicio de auditoría de biblioteca multimedia.

Responsabilidad: analizar una colección de archivos multimedia y generar un
informe estadístico agregado con métricas sobre idiomas, códecs, y posibles
anomalías (archivos sin subtítulos, sin audio en español, o con pistas
duplicadas).

No depende de ninguna capa de UI — devuelve un AuditReport puro que la capa
de presentación puede renderizar como desee.
"""

from typing import Dict, List

from models.schemas import AuditReport, MediaFile


class AuditService:
    """Genera estadísticas agregadas sobre una colección de archivos multimedia.

    Recibe una lista de MediaFile ya analizados por el repositorio y construye
    un informe resumido con contadores de idiomas, códecs y métricas de calidad.
    """

    def build_report(self, files: List[MediaFile]) -> AuditReport:
        """Construye un informe de auditoría completo.

        Args:
            files: Lista de MediaFile con sus pistas ya parseadas.

        Returns:
            AuditReport con métricas agregadas y la lista detallada de archivos.
        """
        audio_languages: Dict[str, int] = {}
        subtitle_languages: Dict[str, int] = {}
        video_codecs: Dict[str, int] = {}
        audio_codecs: Dict[str, int] = {}

        files_without_subtitles = 0
        files_without_spanish_audio = 0
        files_with_duplicate_candidate_audio = 0

        for media_file in files:
            # Detección de anomalías por archivo
            has_subtitles = len(media_file.subtitle_tracks) > 0
            has_spanish_audio = any(
                t.language in {"spa", "es", "esp"} for t in media_file.audio_tracks
            )

            if not has_subtitles:
                files_without_subtitles += 1

            if not has_spanish_audio:
                files_without_spanish_audio += 1

            # Contadores de pistas de vídeo
            seen_audio_signatures = set()
            duplicate_candidate = False

            for video in media_file.video_tracks:
                video_codecs[video.codec] = video_codecs.get(video.codec, 0) + 1

            # Contadores de pistas de audio + detección de duplicados
            for audio in media_file.audio_tracks:
                audio_languages[audio.language] = audio_languages.get(audio.language, 0) + 1
                audio_codecs[audio.codec] = audio_codecs.get(audio.codec, 0) + 1

                signature = (audio.language, audio.codec, audio.channels)
                if signature in seen_audio_signatures:
                    duplicate_candidate = True
                seen_audio_signatures.add(signature)

            # Contadores de pistas de subtítulos
            for sub in media_file.subtitle_tracks:
                subtitle_languages[sub.language] = subtitle_languages.get(sub.language, 0) + 1

            if duplicate_candidate:
                files_with_duplicate_candidate_audio += 1

        return AuditReport(
            total_files=len(files),
            audio_languages=audio_languages,
            subtitle_languages=subtitle_languages,
            video_codecs=video_codecs,
            audio_codecs=audio_codecs,
            files_without_subtitles=files_without_subtitles,
            files_without_spanish_audio=files_without_spanish_audio,
            files_with_duplicate_candidate_audio=files_with_duplicate_candidate_audio,
            detailed_files=files,
        )
