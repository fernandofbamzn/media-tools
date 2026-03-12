"""
Servicio de planificación de limpieza de pistas multimedia.

Responsabilidad: dado un MediaFile y una lista de idiomas a conservar,
generar un CleanPlan que especifica qué pistas mantener y cuáles eliminar.

Reglas de decisión:
  - Las pistas de vídeo se conservan siempre.
  - Las pistas de audio/subtítulos en idiomas permitidos se conservan.
  - Las pistas con idioma "und" (indefinido) se conservan por seguridad.
  - Las pistas forzadas se conservan independientemente del idioma.
  - El resto se marca para eliminación.

No ejecuta la limpieza — eso lo hace MediaService.execute_clean_plan().
"""

from typing import List

from models.schemas import ActionType, CleanPlan, MediaFile, TrackAction


class CleanService:
    """Genera planes de limpieza para archivos multimedia individuales.

    Aplica las reglas de filtrado de idiomas para determinar qué pistas
    conservar y cuáles marcar para eliminación. El resultado es un CleanPlan
    que puede ser revisado/editado por el usuario antes de su ejecución.
    """

    def build_plan(self, media_file: MediaFile, keep_languages: List[str]) -> CleanPlan:
        """Genera un plan de acción sugerido basado en las reglas de idioma.

        Args:
            media_file: Archivo multimedia con sus pistas analizadas.
            keep_languages: Lista de códigos de idioma a conservar (ej: ["spa", "eng"]).

        Returns:
            CleanPlan con una TrackAction por cada pista del archivo,
            indicando si se mantiene (KEEP) o se elimina (REMOVE) y por qué.
        """
        actions: List[TrackAction] = []
        keep_set = {lang.lower() for lang in keep_languages}

        for track in media_file.tracks:
            # Las pistas de vídeo se conservan siempre
            if track.type == "video":
                actions.append(TrackAction(track, ActionType.KEEP, "Pista de vídeo principal"))
                continue

            # Evaluar si el idioma está en la lista de permitidos
            is_valid_lang = track.language.lower() in keep_set or track.language.lower() == "und"

            if is_valid_lang:
                reason = "Idioma en lista de permitidos" if track.language != "und" else "Idioma indefinido"
                actions.append(TrackAction(track, ActionType.KEEP, reason))
            elif track.forced:
                actions.append(TrackAction(track, ActionType.KEEP, "Pista forzada por diseño"))
            else:
                actions.append(TrackAction(track, ActionType.REMOVE, "Idioma no requerido"))

        return CleanPlan(media_file=media_file, track_actions=actions, keep_languages=keep_languages)
