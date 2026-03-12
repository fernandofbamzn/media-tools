"""
Componentes visuales ESPECÍFICOS de media-tools.
Todo lo genérico (clear_screen, pause, show_header, etc.) se importa de clibaseapp.
"""

from rich.tree import Tree

from clibaseapp import clear_screen, console, dict_table, show_error, show_header, show_info, show_success, show_warning
from models.schemas import AuditSummary, BrowseResult, DoctorResult


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
                label = f"[cyan]{t.language}[/cyan]" 
                audio_node.add("[" + label + "] " + f"{t.codec}{channels}{name_info}{default_tag}")

        # Subtítulos
        if media_file.subtitle_tracks:
            sub_node = tree.add("💬 [bold]Subtítulos[/bold]")
            for t in media_file.subtitle_tracks:
                name_info = f" - {t.name}" if t.name else ""
                forced_tag = " [bold red](Forzados)[/bold red]" if t.forced else ""
                default_tag = " [bold green](Por defecto)[/bold green]" if t.default and not t.forced else ""
                label = f"[cyan]{t.language}[/cyan]"
                sub_node.add("[" + label + "] " + f"{t.codec}{name_info}{forced_tag}{default_tag}")

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
