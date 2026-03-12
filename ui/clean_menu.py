"""
Menús interactivos para la resolución del plan de limpieza.
"""

from typing import List

import questionary
from questionary import Choice

from models.schemas import ActionType, CleanPlan, TrackAction
from ui.components import show_header, show_info


def ask_clean_plan(plan: CleanPlan) -> CleanPlan:
    """Muestra un checklist para que el usuario confirme las pistas a mantener."""
    show_header(f"Plan de limpieza: {plan.media_file.path.name}", icon="🧹")

    choices: List[Choice] = []
    
    # Preparamos las opciones, agrupando por tipo
    for action in plan.track_actions:
        track = action.track
        
        # Saltamos la pista de vídeo principal para no abrumar ni permitir que se borre por error
        if track.type == "video":
            continue

        icon = "🔊" if track.type == "audio" else "💬"
        name_part = f" - {track.name}" if track.name else ""
        channels_part = f" ({track.channels}ch)" if track.channels else ""
        
        title = f"{icon} [{track.language}] {track.codec}{channels_part}{name_part}"
        if track.forced:
            title += " (Forzado)"
        if track.default:
            title += " (Por Defecto)"
        
        is_checked = action.action == ActionType.KEEP
        
        choices.append(Choice(title=title, value=action, checked=is_checked))

    if not choices:
        show_info("No hay pistas de audio o subtítulos para modificar en este archivo.")
        return plan

    selected_actions = questionary.checkbox(
        message="Selecciona las pistas que deseas MANTENER (espacio para marcar/desmarcar):",
        choices=choices,
        style=questionary.Style([
            ('highlighted', 'fg:cyan bold'),
            ('selected', 'fg:green bold')
        ])
    ).ask()

    # Si se cancela con Ctrl+C, selected_actions será None
    if selected_actions is None:
        raise KeyboardInterrupt()

    # Actualizamos el plan original
    for action in plan.track_actions:
        if action.track.type == "video":
            continue # Video siempre keep
            
        if action in selected_actions:
            action.action = ActionType.KEEP
            action.reason = "Seleccionado por el usuario"
        else:
            action.action = ActionType.REMOVE
            action.reason = "Desmarcado por el usuario"

    return plan
