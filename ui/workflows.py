"""
Workflows interactivos específicos de media-tools.

Este módulo concentra toda la conversación con el usuario para que la
capa `services/` permanezca libre de dependencias de interfaz.
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
from models.schemas import AuditSummary, CleanPlan
from services.media_service import CleanFailure, CleanResult, MediaService, VIDEO_EXTENSIONS
from ui.clean_menu import ask_global_clean_plans
from ui.components import render_audit_summary


def _format_bytes(size: int) -> str:
    """Formatea un tamaño en bytes a una unidad legible."""

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:3.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def browse_media(config: ConfigManager) -> Optional[BrowseResult]:
    """Abre el navegador interactivo usando la raíz configurada para la app."""

    browser = BrowserMenu(file_extensions=VIDEO_EXTENSIONS, file_icon="🎬")
    return browser.browse(load_media_root(config))


def run_clean_workflow(service: MediaService, config: ConfigManager) -> None:
    """Ejecuta el flujo interactivo completo de limpieza de pistas.

    El workflow resuelve la configuración y el input del usuario, delega
    las reglas de negocio al servicio y renderiza el resultado final.
    """

    clear_screen()
    show_header("Limpiador de Pistas", "Inicio > Limpieza", icon="🧹")

    selected = browse_media(config)
    if selected is None:
        show_warning("Selección cancelada.")
        return

    audit_summary = service.audit(selected)
    render_audit_summary(audit_summary)
    if not _should_continue_after_audit(audit_summary):
        return

    keep_languages = _ask_keep_languages(config)
    if keep_languages is None:
        return

    plans = service.build_clean_plans_from_media_files(
        audit_summary.report.detailed_files,
        keep_languages,
    )

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


def _should_continue_after_audit(summary: AuditSummary) -> bool:
    """Decide si el flujo debe continuar tras mostrar la auditoría."""

    if summary.cancelled:
        return False

    if summary.report is None:
        return False

    should_continue = bool(questionary.confirm("¿Continuar con la planificación de limpieza?").ask())
    if not should_continue:
        show_warning("Limpieza cancelada.")
    return should_continue


def _ask_keep_languages(config: ConfigManager) -> Optional[List[str]]:
    """Solicita idiomas extra a conservar para la ejecución actual.

    Devuelve `None` si el usuario cancela el prompt inicial.
    """

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
    """Ejecuta planes con barra de progreso y devuelve el resultado agregado.

    La captura de errores se realiza aquí para mantener el feedback visual
    sincronizado con el archivo que se está procesando.
    """

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
    """Renderiza el resultado final de la limpieza.

    Si hubo errores parciales, los lista después del resumen para que el
    usuario sepa qué archivos requieren revisión manual.
    """

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
