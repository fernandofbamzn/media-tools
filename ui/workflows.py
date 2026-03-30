"""Workflows interactivos especificos de media-tools."""

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
from models.schemas import AuditSummary, CleanPlan, OptimizationProfile, OptimizePlan
from services.media_service import (
    CleanFailure,
    CleanResult,
    MediaService,
    OptimizeFailure,
    OptimizeResult,
    VIDEO_EXTENSIONS,
)
from ui.clean_menu import ask_global_clean_plans
from ui.components import render_audit_summary, render_optimize_plan_summary


def _format_bytes(size: int) -> str:
    negative = size < 0
    size = abs(size)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            prefix = "-" if negative else ""
            return f"{prefix}{size:3.1f} {unit}"
        size /= 1024.0
    prefix = "-" if negative else ""
    return f"{prefix}{size:.1f} PB"


def browse_media(config: ConfigManager) -> Optional[BrowseResult]:
    browser = BrowserMenu(file_extensions=VIDEO_EXTENSIONS, file_icon="🎬")
    return browser.browse(load_media_root(config))


def run_clean_workflow(service: MediaService, config: ConfigManager) -> None:
    clear_screen()
    show_header("Limpiador de Pistas", "Inicio > Multimedia > Limpieza", icon="🧹")

    selected = browse_media(config)
    if selected is None:
        show_warning("Seleccion cancelada.")
        return

    audit_summary = service.audit(selected)
    render_audit_summary(audit_summary)
    if not _should_continue_after_audit(audit_summary, "planificacion de limpieza"):
        return

    keep_languages = _ask_keep_languages(config)
    if keep_languages is None:
        return

    plans = service.build_clean_plans_from_media_files(audit_summary.report.detailed_files, keep_languages)

    try:
        final_plans = ask_global_clean_plans(plans)
    except KeyboardInterrupt:
        show_warning("\nPlanificacion cancelada.")
        return

    plans_to_execute = _render_clean_plan_summary(final_plans)
    if not plans_to_execute:
        show_success("Los archivos ya cumplen con la seleccion. Nada que borrar.")
        return

    total_remove = sum(len(plan.tracks_to_remove) for plan in plans_to_execute)
    show_warning(f"ATENCION: {total_remove} pistas en {len(plans_to_execute)} archivos seran eliminadas.")

    if not questionary.confirm("¿Aplicar cambios? (destructivo)").ask():
        show_warning("Cancelado.")
        return

    result = _execute_plans_with_progress(service, plans_to_execute)
    _render_clean_result(result)


def run_optimize_workflow(service: MediaService, config: ConfigManager) -> None:
    clear_screen()
    show_header("Optimizacion de Tamano", "Inicio > Multimedia > Optimizacion", icon="⚙️")

    selected = browse_media(config)
    if selected is None:
        show_warning("Seleccion cancelada.")
        return

    audit_summary = service.audit(selected)
    render_audit_summary(audit_summary)
    if not _should_continue_after_audit(audit_summary, "optimizacion"):
        return

    profile = _ask_optimization_profile(service)
    if profile is None:
        show_warning("Optimizacion cancelada.")
        return

    plans = service.build_optimize_plans_from_media_files(
        audit_summary.report.detailed_files,
        profile_id=profile.id,
    )
    executable_plans = render_optimize_plan_summary(plans)
    if not executable_plans:
        show_warning("No hay archivos aptos para optimizar en esta seleccion.")
        return

    approx_saved = sum(plan.original_size - plan.estimated_size for plan in executable_plans)
    show_info(f"Ahorro estimado aproximado: {_format_bytes(approx_saved)}")

    if not questionary.confirm("¿Generar copias optimizadas?").ask():
        show_warning("Optimizacion cancelada.")
        return

    result = _execute_optimize_plans_with_progress(service, plans)
    _render_optimize_result(result)

    if result.outputs and questionary.confirm("¿Reemplazar los originales por las copias optimizadas?").ask():
        failures = service.replace_originals_with_optimized(result.outputs)
        if failures:
            for failure in failures:
                show_error(f"{failure.file_path.name}: {failure.message}")
        else:
            show_success("Originales reemplazados por las copias optimizadas.")


def _should_continue_after_audit(summary: AuditSummary, target: str) -> bool:
    if summary.cancelled or summary.report is None:
        return False

    should_continue = bool(questionary.confirm(f"¿Continuar con la {target}?").ask())
    if not should_continue:
        show_warning("Operacion cancelada.")
    return should_continue


def _ask_keep_languages(config: ConfigManager) -> Optional[List[str]]:
    keep_languages = load_keep_languages(config)
    extra_languages = questionary.text(
        f"Idiomas a conservar: {', '.join(keep_languages)}.\n"
        "¿Anadir para ESTA ejecucion? (vacio = ninguno):"
    ).ask()

    if extra_languages is None:
        return None
    if not extra_languages.strip():
        return keep_languages

    return keep_languages + [
        language.strip().lower()
        for language in extra_languages.split(",")
        if language.strip()
    ]


def _ask_optimization_profile(service: MediaService) -> Optional[OptimizationProfile]:
    profiles = service.list_optimization_profiles()
    choices = [
        questionary.Choice(f"{profile.title} ({profile.id})", value=profile)
        for profile in profiles
    ]
    return questionary.select("Selecciona un perfil de optimizacion:", choices=choices).ask()


def _render_clean_plan_summary(plans: List[CleanPlan]) -> List[CleanPlan]:
    clear_screen()
    show_header("Resumen del Plan", "Inicio > Multimedia > Limpieza > Resumen", icon="📝")
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


def _execute_optimize_plans_with_progress(service: MediaService, plans: List[OptimizePlan]) -> OptimizeResult:
    outputs = []
    skipped = []
    failures: List[OptimizeFailure] = []
    executable_total = sum(1 for plan in plans if plan.can_optimize)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task("Optimizando...", total=max(executable_total, 1))
        for plan in plans:
            if not plan.can_optimize:
                skipped.append(plan)
                continue

            progress.update(task_id, description=f"Optimizando: {plan.media_file.path.name}...")
            try:
                outputs.append(service.execute_optimize_plan(plan))
            except Exception as exc:
                failures.append(OptimizeFailure(file_path=plan.media_file.path, message=str(exc)))
            progress.advance(task_id)

    return OptimizeResult(
        files_processed=len(plans),
        files_optimized=len(outputs),
        files_skipped=len(skipped),
        files_with_errors=len(failures),
        bytes_saved=sum(output.bytes_saved for output in outputs),
        outputs=outputs,
        skipped=skipped,
        failures=failures,
    )


def _render_clean_result(result: CleanResult) -> None:
    clear_screen()
    show_header("Limpieza Completada", icon="🎉")
    message = (
        f"Procesados: {result.files_processed - result.files_with_errors}/{result.files_processed}\n"
        f"Espacio recuperado: {_format_bytes(result.bytes_saved)}"
    )

    if result.files_with_errors == 0:
        show_success(message)
        return

    show_warning(f"{message}\n{result.files_with_errors} errores.")
    for failure in result.failures:
        show_error(f"{failure.file_path.name}: {failure.message}")


def _render_optimize_result(result: OptimizeResult) -> None:
    clear_screen()
    show_header("Optimizacion Completada", icon="🎛️")
    show_info(
        f"Optimizados: {result.files_optimized} | Omitidos: {result.files_skipped} | "
        f"Errores: {result.files_with_errors}"
    )
    show_success(f"Ahorro total real: {_format_bytes(result.bytes_saved)}")

    for output in result.outputs:
        show_info(
            f"{output.input_path.name} -> {output.output_path.name} | "
            f"{_format_bytes(output.bytes_saved)}"
        )

    for skipped in result.skipped:
        show_warning(f"{skipped.media_file.path.name}: omitido ({skipped.skip_reason})")

    for failure in result.failures:
        show_error(f"{failure.file_path.name}: {failure.message}")
