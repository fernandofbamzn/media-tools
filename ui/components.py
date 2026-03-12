"""
Componentes visuales ESPECÍFICOS de media-tools.
Todo lo genérico viene de clibaseapp. Usa fmt para formato normalizado.
"""

from rich.tree import Tree

from clibaseapp import clear_screen, console, dict_table, fmt, show_header, show_info, show_success, show_warning
from models.schemas import AuditSummary


def render_audit_summary(summary: AuditSummary) -> None:
    """Renderiza resumen de auditoría multimedia."""
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

    for media_file in summary.report.detailed_files:
        title = f"🎬 {fmt.tag(media_file.path.name, 'bold cyan')} {fmt.dim(f'({media_file.container})')}"
        tree = Tree(title)

        if media_file.video_tracks:
            video_node = tree.add(f"🎞️ {fmt.bold('Vídeo')}")
            for t in media_file.video_tracks:
                name_info = f" - {t.name}" if t.name else ""
                video_node.add(f"[{t.language}] {t.codec}{name_info}")

        if media_file.audio_tracks:
            audio_node = tree.add(f"🔊 {fmt.bold('Audio')}")
            for t in media_file.audio_tracks:
                name_info = f" - {t.name}" if t.name else ""
                channels = f" ({t.channels}ch)" if t.channels else ""
                default_tag = f" {fmt.tag('(Por defecto)', 'bold green')}" if t.default else ""
                lang = fmt.tag(t.language, "cyan")
                audio_node.add("[" + lang + "] " + f"{t.codec}{channels}{name_info}{default_tag}")

        if media_file.subtitle_tracks:
            sub_node = tree.add(f"💬 {fmt.bold('Subtítulos')}")
            for t in media_file.subtitle_tracks:
                name_info = f" - {t.name}" if t.name else ""
                forced_tag = f" {fmt.tag('(Forzados)', 'bold red')}" if t.forced else ""
                default_tag = f" {fmt.tag('(Por defecto)', 'bold green')}" if t.default and not t.forced else ""
                lang = fmt.tag(t.language, "cyan")
                sub_node.add("[" + lang + "] " + f"{t.codec}{name_info}{forced_tag}{default_tag}")

        console.print(tree)
        console.print()

    console.print()
    show_header("Resumen Global", icon="📈")
    console.print(dict_table("Idiomas de audio", summary.report.audio_languages, "Idioma", "Pistas"))
    console.print(dict_table("Idiomas de subtítulos", summary.report.subtitle_languages, "Idioma", "Pistas"))
    console.print(dict_table("Códecs de vídeo", summary.report.video_codecs, "Códec", "Pistas"))
    console.print(dict_table("Códecs de audio", summary.report.audio_codecs, "Códec", "Pistas"))

    show_info(f"Archivos sin subtítulos: {summary.report.files_without_subtitles}")
    show_info(f"Archivos sin audio en español: {summary.report.files_without_spanish_audio}")
    show_info(f"Archivos con posible audio duplicado: {summary.report.files_with_duplicate_candidate_audio}")
