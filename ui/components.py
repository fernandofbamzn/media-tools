"""
Componentes visuales reutilizables.
"""

from typing import Dict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from models.schemas import AuditSummary, BrowseResult, DoctorResult
from ui.theme import APP_THEME

console = Console(theme=APP_THEME)


def clear_screen() -> None:
    """Limpia la terminal."""
    console.clear()


def pause() -> None:
    """Pausa la ejecución hasta que el usuario pulse Enter."""
    console.print()
    console.print("[dim]Pulsar Enter para continuar...[/dim]", end="")
    input()
    console.print()


def show_header(title: str, breadcrumb: str = "", icon: str = "") -> None:
    """Renderiza encabezado principal con breadcrumb e icono opcional."""
    if breadcrumb:
        console.print(f"[breadcrumb]📍 {breadcrumb}[/breadcrumb]")
    
    title_text = f"{icon} {title}" if icon else title
    console.print(Panel(f"[header]{title_text}[/header]", border_style="cyan", padding=(1, 2), expand=False))


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
    table = Table(title=f"📊 [bold]{title}[/bold]", show_lines=True, header_style="bold cyan", expand=True)
    table.add_column(key_label, style="cyan", justify="left")
    table.add_column(value_label, justify="right", style="green", width=15)

    for key, value in sorted(values.items(), key=lambda x: (-x[1], x[0])):
        table.add_row(str(key), str(value))

    return table


def render_doctor_result(result: DoctorResult) -> None:
    """Renderiza el diagnóstico de sistema."""
    clear_screen()
    show_header("Media Tools Doctor", "Inicio > Doctor", icon="🩺")
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
    clear_screen()
    show_header("Navegador de Biblioteca", "Inicio > Navegación", icon="📁")
    if result is None:
        show_warning("Navegación cancelada.")
        return
    show_success(f"Seleccionado: {result.selected_path}")
    show_info(f"Tipo de selección: {result.selection_type}")


def render_audit_summary(summary: AuditSummary) -> None:
    """Renderiza resumen de auditoría."""
    clear_screen()
    show_header("Auditoría de Biblioteca", "Inicio > Auditoría", icon="🔍")

    if summary.cancelled:
        show_warning("Auditoría cancelada.")
        return

    if summary.report is None:
        show_warning("No se encontraron archivos multimedia.")
        return

    show_info(f"Analizando {summary.scanned_files} archivos...")
    show_success(f"Archivos analizados: {summary.report.total_files}")
    console.print()

    # Desglose de archivos e información detallada de pistas por archivo
    for media_file in summary.report.detailed_files:
        tree = Tree(f"🎬 [bold cyan]{media_file.path.name}[/bold cyan] [dim]({media_file.container})[/dim]")

        # Video
        if media_file.video_tracks:
            video_node = tree.add("🎞️ [bold]Vídeo[/bold]")
            for t in media_file.video_tracks:
                name_info = f" - {t.name}" if t.name else ""
                video_node.add(f"[{t.language}] {t.codec}{name_info}")

        # Audio
        if media_file.audio_tracks:
            audio_node = tree.add("🔊 [bold]Audio[/bold]")
            for t in media_file.audio_tracks:
                name_info = f" - {t.name}" if t.name else ""
                channels = f" ({t.channels}ch)" if t.channels else ""
                default_tag = " [bold green](Por defecto)[/bold green]" if t.default else ""
                audio_node.add(f"\[[cyan]{t.language}[/cyan]] {t.codec}{channels}{name_info}{default_tag}")

        # Subtítulos
        if media_file.subtitle_tracks:
            sub_node = tree.add("💬 [bold]Subtítulos[/bold]")
            for t in media_file.subtitle_tracks:
                name_info = f" - {t.name}" if t.name else ""
                forced_tag = " [bold red](Forzados)[/bold red]" if t.forced else ""
                default_tag = " [bold green](Por defecto)[/bold green]" if t.default and not t.forced else ""
                sub_node.add(f"\[[cyan]{t.language}[/cyan]] {t.codec}{name_info}{forced_tag}{default_tag}")

        console.print(tree)
        console.print()

    # Resumen general (Métricas)
    console.print()
    show_header("Resumen Global", icon="📈")
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
