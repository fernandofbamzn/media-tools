"""
Workflows interactivos específicos de media-tools.
"""

from typing import List, Optional

import questionary
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from clibaseapp import (
    BrowserMenu,
    BrowseResult,
    ConfigManager,
    clear_screen,
    console,
    fmt,
    show_error,
    show_header,
    show_info,
    show_success,
    show_warning,
)
from core.config import load_keep_languages, load_media_root
from models.schemas import ActionType, CleanPlan
from services.media_service import CleanFailure, CleanResult, MediaService, VIDEO_EXTENSIONS
from ui.clean_menu import ask_global_clean_plans


def _format_bytes(size: int) -> str:
    """Formatea un tamaño en bytes a una unidad legible."""

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:3.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def browse_media(config: ConfigManager) -> Optional[BrowseResult]:
    """Abre el navegador interactivo de archivos multimedia."""

    browser = BrowserMenu(file_extensions=VIDEO_EXTENSIONS, file_icon="🎬")
    return browser.browse(load_media_root(config))


def run_clean_workflow(service: MediaService, config: ConfigManager) -> None:
    """Ejecuta el flujo interactivo completo de limpieza de pistas."""

    clear_screen()
    show_header("Limpiador de Pistas", "Inicio > Limpieza", icon="🧹")

    keep_languages = _ask_keep_languages(config)
    if keep_languages is None:
        return

    selected = browse_media(config)
    if selected is None:
        show_warning("Selección cancelada.")
        return

    plans = service.build_clean_plans(selected, keep_languages)
    if not plans:
        show_warning("No se encontraron archivos multimedia para limpiar.")
        return

    try:
        final_plans = ask_global_clean_plans(plans)
    except KeyboardInterrupt:
        show_warning("\nPlanificación cancelada.")
        return

    plans_to_execute = _render_plan_summary(final_plans)
    if not plans_to_execute:
        show_success("Los archivos ya cumplen con la selección. Nada que borrar.")
        return

    total_remove = sum(len(plan.tracks_to_remove) for plan in plans_to_execute)
    show_warning(
        f"ATENCIÓN: {total_remove} pistas en {len(plans_to_execute)} archivos serán eliminadas."
    )

    if not questionary.confirm("¿Aplicar cambios? (destructivo)").ask():
        show_warning("Cancelado.")
        return

    result = _execute_plans_with_progress(service, plans_to_execute)
    _render_clean_result(result)


def _ask_keep_languages(config: ConfigManager) -> Optional[List[str]]:
    """Solicita idiomas extra a conservar para la ejecución actual."""

    keep_languages = load_keep_languages(config)
    extra_languages = questionary.text(
        f"Idiomas a conservar: {', '.join(keep_languages)}.\n"
        "¿Añadir para ESTA ejecución? (vacío = ninguno):"
    ).ask()

    if extra_languages is None:
        return None

    if not extra_languages.strip():
        return keep_languages

    merged_languages = keep_languages + [
        language.strip().lower()
        for language in extra_languages.split(",")
        if language.strip()
    ]
    return merged_languages


def _render_plan_summary(plans: List[CleanPlan]) -> List[CleanPlan]:
    """Muestra el resumen del plan y devuelve solo los archivos con cambios."""

    clear_screen()
    show_header("Resumen del Plan", "Inicio > Limpieza > Resumen", icon="📝")
    plans_to_execute: List[CleanPlan] = []

    for plan in plans:
        to_keep = len(plan.tracks_to_keep)
        to_remove = len(plan.tracks_to_remove)
        show_info(f"🎬 {plan.media_file.path.name}")
        console.print(
            f"   {fmt.tag(f'+ {to_keep} conservar', 'green')} | "
            f"{fmt.tag(f'- {to_remove} eliminar', 'red')}\n"
        )
        if to_remove > 0:
            plans_to_execute.append(plan)

    return plans_to_execute


def _execute_plans_with_progress(service: MediaService, plans: List[CleanPlan]) -> CleanResult:
    """Ejecuta planes con barra de progreso y devuelve el resultado agregado."""

    total_saved = 0
    failures: List[CleanFailure] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task("Limpiando...", total=len(plans))
        for plan in plans:
            progress.update(task_id, description=f"Limpiando: {plan.media_file.path.name}...")
            try:
                total_saved += service.execute_clean_plan(plan)
            except Exception as exc:
                failures.append(CleanFailure(file_path=plan.media_file.path, message=str(exc)))
            progress.advance(task_id)

    return CleanResult(
        files_processed=len(plans),
        files_with_errors=len(failures),
        bytes_saved=total_saved,
        failures=failures,
    )


def _render_clean_result(result: CleanResult) -> None:
    """Renderiza el resultado final de la limpieza."""

    clear_screen()
    show_header("✨ Limpieza Completada ✨", icon="🎉")
    message = (
        f"Procesados: {result.files_processed - result.files_with_errors}/{result.files_processed}\n"
        f"Espacio: {_format_bytes(result.bytes_saved)}"
    )

    if result.files_with_errors == 0:
        show_success(message)
        return

    show_warning(f"{message}\n{result.files_with_errors} errores.")
    for failure in result.failures:
        show_error(f"{failure.file_path.name}: {failure.message}")
