"""
Componentes visuales reutilizables.
"""

from typing import Dict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from models.schemas import AuditSummary, BrowseResult, DoctorResult
from ui.theme import APP_THEME

console = Console(theme=APP_THEME)


def show_header(title: str, breadcrumb: str = "") -> None:
    """Renderiza encabezado principal con breadcrumb."""
    if breadcrumb:
        console.print(f"[breadcrumb]{breadcrumb}[/breadcrumb]")
    console.print(Panel(f"[header]{title}[/header]", border_style="cyan"))


def show_info(text: str) -> None:
    """Mensaje informativo."""
    console.print(f"[info]ℹ {text}[/info]")


def show_success(text: str) -> None:
    """Mensaje de éxito."""
    console.print(f"[success]✔ {text}[/success]")


def show_warning(text: str) -> None:
    """Mensaje de advertencia."""
    console.print(f"[warning]⚠ {text}[/warning]")


def show_error(text: str) -> None:
    """Mensaje de error."""
    console.print(f"[error]✖ {text}[/error]")


def dict_table(title: str, values: Dict[str, int], key_label: str, value_label: str) -> Table:
    """Construye una tabla Rich a partir de un diccionario."""
    table = Table(title=title, show_lines=False)
    table.add_column(key_label, style="cyan")
    table.add_column(value_label, justify="right", style="green")

    for key, value in sorted(values.items(), key=lambda x: (-x[1], x[0])):
        table.add_row(str(key), str(value))

    return table


def render_doctor_result(result: DoctorResult) -> None:
    """Renderiza el diagnóstico de sistema."""
    show_header("Media Tools Doctor", "Inicio > Doctor")
    for check in result.checks:
        if check.available:
            show_success(f"{check.name} encontrado")
        else:
            show_error(f"{check.name} NO encontrado")

    if result.media_root_exists:
        show_success(f"Raíz multimedia accesible: {result.media_root}")
    else:
        show_warning(f"No existe la raíz multimedia: {result.media_root}")


def render_browse_result(result: BrowseResult | None) -> None:
    """Renderiza el resultado de navegación."""
    show_header("Navegador de Biblioteca", "Inicio > Navegación")
    if result is None:
        show_warning("Navegación cancelada.")
        return
    show_success(f"Seleccionado: {result.selected_path}")
    show_info(f"Tipo de selección: {result.selection_type}")


def render_audit_summary(summary: AuditSummary) -> None:
    """Renderiza resumen de auditoría."""
    show_header("Auditoría de Biblioteca", "Inicio > Auditoría")

    if summary.cancelled:
        show_warning("Auditoría cancelada.")
        return

    if summary.report is None:
        show_warning("No se encontraron archivos multimedia.")
        return

    show_info(f"Analizando {summary.scanned_files} archivos...")
    show_success(f"Archivos analizados: {summary.report.total_files}")
    console.print(dict_table("Idiomas de audio", summary.report.audio_languages, "Idioma", "Pistas"))
    console.print(
        dict_table("Idiomas de subtítulos", summary.report.subtitle_languages, "Idioma", "Pistas")
    )
    console.print(dict_table("Códecs de vídeo", summary.report.video_codecs, "Códec", "Pistas"))
    console.print(dict_table("Códecs de audio", summary.report.audio_codecs, "Códec", "Pistas"))

    show_info(f"Archivos sin subtítulos: {summary.report.files_without_subtitles}")
    show_info(f"Archivos sin audio en español: {summary.report.files_without_spanish_audio}")
    show_info(
        "Archivos con posible audio duplicado: "
        f"{summary.report.files_with_duplicate_candidate_audio}"
    )
