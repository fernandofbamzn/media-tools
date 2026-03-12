"""
Servicio para la planificación y ejecución de limpieza de pistas (Business Logic).
"""

from typing import List
from models.schemas import ActionType, CleanPlan, MediaFile, TrackAction


class CleanService:
    """Lógica para limpiar archivos multimedia de audios y subtítulos indeseados."""

    def build_plan(self, media_file: MediaFile, keep_languages: List[str]) -> CleanPlan:
        """Genera un plan de acción sugerido basado en las reglas globales."""
        actions: List[TrackAction] = []
        keep_set = {lang.lower() for lang in keep_languages}

        for track in media_file.tracks:
            # Por defecto siempre mantener video
            if track.type == "video":
                actions.append(TrackAction(track, ActionType.KEEP, "Pista de vídeo principal"))
                continue

            # Mantener si es idioma configurado o la pista está forzada
            is_valid_lang = track.language.lower() in keep_set or track.language.lower() == "und"
            
            if is_valid_lang:
                reason = "Idioma en lista de permitidos" if track.language != "und" else "Idioma indefinido"
                actions.append(TrackAction(track, ActionType.KEEP, reason))
            elif track.forced:
                actions.append(TrackAction(track, ActionType.KEEP, "Pista forzada por diseño"))
            else:
                actions.append(TrackAction(track, ActionType.REMOVE, "Idioma no requerido"))

        return CleanPlan(media_file=media_file, track_actions=actions, keep_languages=keep_languages)
