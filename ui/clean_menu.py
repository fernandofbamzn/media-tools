"""
Menús interactivos para la resolución del plan de limpieza.
"""

from typing import List, Tuple

import questionary
from questionary import Choice

from models.schemas import ActionType, CleanPlan, TrackAction
from ui.components import clear_screen, show_error, show_header, show_info, show_warning


def _track_signature(track) -> Tuple:
    """Devuelve la firma única de una pista para agruparla globalmente."""
    return (track.type, track.language, track.codec, track.channels, track.name, track.forced, track.default)


def ask_global_clean_plans(plans: List[CleanPlan]) -> List[CleanPlan]:
    """Muestra un checklist global agrupado y aplica los cambios a todos los planes."""
    if not plans:
        return []

    while True:
        clear_screen()
        if len(plans) == 1:
            show_header(f"Plan de limpieza: {plans[0].media_file.path.name}", icon="🧹")
        else:
            show_header(f"Plan de limpieza global ({len(plans)} archivos)", icon="🧹")

        unique_tracks = {}
        for plan in plans:
            for action in plan.track_actions:
                track = action.track
                if track.type == "video":
                    continue
                
                sig = _track_signature(track)
                if sig not in unique_tracks:
                    unique_tracks[sig] = {
                        "track": track,
                        "keep": action.action == ActionType.KEEP
                    }
                else:
                    if action.action == ActionType.KEEP:
                        unique_tracks[sig]["keep"] = True

        choices: List[Choice] = []
        for sig, data in unique_tracks.items():
            track = data["track"]
            icon = "🔊" if track.type == "audio" else "💬"
            name_part = f" - {track.name}" if track.name else ""
            channels_part = f" ({track.channels}ch)" if track.channels else ""
            
            title = f"{icon} [{track.language}] {track.codec}{channels_part}{name_part}"
            if track.forced:
                title += " (Forzado)"
            if track.default:
                title += " (Por Defecto)"
            
            choices.append(Choice(title=title, value=sig, checked=data["keep"]))

        if not choices:
            show_info("No hay pistas de audio o subtítulos para modificar en la selección.")
            return plans

        selected_sigs = questionary.checkbox(
            message="Selecciona las pistas que deseas MANTENER (espacio para marcar/desmarcar):",
            choices=choices,
            style=questionary.Style([
                ('highlighted', 'fg:cyan bold'),
                ('selected', 'fg:green bold')
            ])
        ).ask()

        if selected_sigs is None:
            raise KeyboardInterrupt()

        # Aplicar la selección a todos los planes
        selected_sig_set = set(selected_sigs)
        for plan in plans:
            for action in plan.track_actions:
                if action.track.type == "video":
                    continue
                
                sig = _track_signature(action.track)
                if sig in selected_sig_set:
                    action.action = ActionType.KEEP
                    action.reason = "Seleccionado globalmente"
                else:
                    action.action = ActionType.REMOVE
                    action.reason = "Desmarcado globalmente"

        # Comprobar si algún archivo se queda sin audios
        needs_edit = False
        final_plans = []
        
        for plan in plans:
            keep_audios = [a for a in plan.track_actions if a.track.type == "audio" and a.action == ActionType.KEEP]
            
            if not keep_audios:
                show_warning(f"\n¡Atención! El archivo '{plan.media_file.path.name}' se quedaría SIN ninguna pista de audio.")
                action = questionary.select(
                    "¿Qué deseas hacer?",
                    choices=[
                        Choice("✏️ Editar selección global", value="edit"),
                        Choice("⏭️ Saltarse este archivo", value="skip"),
                        Choice("⚠️ Continuar y dejar sin audio", value="continue")
                    ]
                ).ask()
                
                if action == "edit":
                    needs_edit = True
                    break
                elif action == "skip":
                    continue
                elif action == "continue":
                    final_plans.append(plan)
            else:
                final_plans.append(plan)

        if needs_edit:
            continue
            
        return final_plans
