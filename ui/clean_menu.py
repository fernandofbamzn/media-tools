"""Menus interactivos para la resolucion del plan de limpieza."""

from typing import List, Tuple

import questionary
from questionary import Choice

from clibaseapp import clear_screen, show_header, show_info, show_warning
from models.schemas import ActionType, CleanPlan, Track
from ui.components import format_track_label


def _track_signature(track: Track) -> Tuple:
    return (
        track.type,
        track.language,
        track.language_ietf,
        track.codec,
        track.channels,
        track.bitrate,
        track.label_name,
        track.forced,
        track.default,
    )


def ask_global_clean_plans(plans: List[CleanPlan]) -> List[CleanPlan]:
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
                    unique_tracks[sig] = {"track": track, "keep": action.action == ActionType.KEEP}
                elif action.action == ActionType.KEEP:
                    unique_tracks[sig]["keep"] = True

        choices: List[Choice] = []
        for sig, data in unique_tracks.items():
            track = data["track"]
            icon = "🔊" if track.type == "audio" else "💬"
            title = f"{icon} {format_track_label(track)}"
            choices.append(Choice(title=title, value=sig, checked=data["keep"]))

        if not choices:
            show_info("No hay pistas de audio o subtitulos para modificar en la seleccion.")
            return plans

        selected_sigs = questionary.checkbox(
            message="Selecciona las pistas que deseas MANTENER:",
            choices=choices,
            style=questionary.Style(
                [
                    ("highlighted", "fg:cyan bold"),
                    ("selected", "fg:green bold"),
                ]
            ),
        ).ask()

        if selected_sigs is None:
            raise KeyboardInterrupt()

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

        needs_edit = False
        final_plans = []
        for plan in plans:
            keep_audios = [
                action
                for action in plan.track_actions
                if action.track.type == "audio" and action.action == ActionType.KEEP
            ]

            if not keep_audios:
                show_warning(
                    f"\nAtencion: el archivo '{plan.media_file.path.name}' se quedaria sin ninguna pista de audio."
                )
                action = questionary.select(
                    "¿Que deseas hacer?",
                    choices=[
                        Choice("✏️ Editar seleccion global", value="edit"),
                        Choice("⏭️ Saltarse este archivo", value="skip"),
                        Choice("⚠️ Continuar y dejar sin audio", value="continue"),
                    ],
                ).ask()

                if action == "edit":
                    needs_edit = True
                    break
                if action == "skip":
                    continue
            final_plans.append(plan)

        if needs_edit:
            continue

        return final_plans
