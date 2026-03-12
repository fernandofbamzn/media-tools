"""
Servicio de auditoría de biblioteca.
"""

from typing import Dict, List

from models.schemas import AuditReport, MediaFile


class AuditService:
    """Genera estadísticas agregadas sobre una colección multimedia."""

    def build_report(self, files: List[MediaFile]) -> AuditReport:
        """Construye el informe de auditoría."""
        audio_languages: Dict[str, int] = {}
        subtitle_languages: Dict[str, int] = {}
        video_codecs: Dict[str, int] = {}
        audio_codecs: Dict[str, int] = {}

        files_without_subtitles = 0
        files_without_spanish_audio = 0
        files_with_duplicate_candidate_audio = 0

        for media_file in files:
            has_subtitles = len(media_file.subtitle_tracks) > 0
            has_spanish_audio = any(t.language in {"spa", "es", "esp"} for t in media_file.audio_tracks)

            if not has_subtitles:
                files_without_subtitles += 1

            if not has_spanish_audio:
                files_without_spanish_audio += 1

            seen_audio_signatures = set()
            duplicate_candidate = False

            for video in media_file.video_tracks:
                video_codecs[video.codec] = video_codecs.get(video.codec, 0) + 1

            for audio in media_file.audio_tracks:
                audio_languages[audio.language] = audio_languages.get(audio.language, 0) + 1
                audio_codecs[audio.codec] = audio_codecs.get(audio.codec, 0) + 1

                signature = (audio.language, audio.codec, audio.channels)
                if signature in seen_audio_signatures:
                    duplicate_candidate = True
                seen_audio_signatures.add(signature)

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
