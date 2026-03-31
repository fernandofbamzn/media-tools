"""Componentes visuales especificos de media-tools."""

from rich.tree import Tree

from clibaseapp import clear_screen, console, dict_table, fmt, show_header, show_info, show_success, show_warning
from models.schemas import AuditSummary, OptimizePlan, Track


def format_bytes(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:3.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def format_bitrate(bitrate: int | None) -> str:
    if bitrate is None:
        return ""
    kbps = round(bitrate / 1000)
    return f"{kbps} kbps"


def format_track_label(track: Track) -> str:
    parts = [track.language]
    if track.language_ietf and track.language_ietf != track.language:
        parts.append(track.language_ietf)
    if track.codec:
        parts.append(track.codec)
    if track.channels:
        parts.append(f"{track.channels}ch")
    bitrate = format_bitrate(track.bitrate)
    if bitrate:
        parts.append(bitrate)
    if track.label_name:
        parts.append(track.label_name)
    if track.forced:
        parts.append("Forzado")
    if track.default:
        parts.append("Por defecto")
    return " | ".join(parts)


def render_audit_summary(summary: AuditSummary) -> None:
    clear_screen()
    show_header("Auditoria de la Seleccion", "Inicio > Multimedia > Auditoria", icon="🔍")

    if summary.cancelled:
        show_warning("Auditoria cancelada.")
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
            video_node = tree.add(f"🎞️ {fmt.bold('Video')}")
            for track in media_file.video_tracks:
                video_node.add(format_track_label(track))

        if media_file.audio_tracks:
            audio_node = tree.add(f"🔊 {fmt.bold('Audio')}")
            for track in media_file.audio_tracks:
                audio_node.add(format_track_label(track))

        if media_file.subtitle_tracks:
            sub_node = tree.add(f"💬 {fmt.bold('Subtitulos')}")
            for track in media_file.subtitle_tracks:
                sub_node.add(format_track_label(track))

        console.print(tree)
        console.print()

    show_header("Resumen Global", icon="📈")
    console.print(dict_table("Idiomas de audio", summary.report.audio_languages, "Idioma", "Pistas"))
    console.print(dict_table("Idiomas de subtitulos", summary.report.subtitle_languages, "Idioma", "Pistas"))
    console.print(dict_table("Codecs de video", summary.report.video_codecs, "Codec", "Pistas"))
    console.print(dict_table("Codecs de audio", summary.report.audio_codecs, "Codec", "Pistas"))

    show_info(f"Archivos sin subtitulos: {summary.report.files_without_subtitles}")
    show_info(f"Archivos sin audio en espanol: {summary.report.files_without_spanish_audio}")
    show_info(f"Archivos con posible audio duplicado: {summary.report.files_with_duplicate_candidate_audio}")


def render_optimize_plan_summary(plans: list[OptimizePlan]) -> list[OptimizePlan]:
    clear_screen()
    show_header("Resumen de Optimizacion", "Inicio > Multimedia > Optimizacion", icon="⚙️")

    executable_plans: list[OptimizePlan] = []
    for plan in plans:
        if plan.can_optimize:
            executable_plans.append(plan)
            show_info(
                f"{plan.media_file.path.name}: {plan.profile.title} | "
                f"{format_bytes(plan.original_size)} -> ~{format_bytes(plan.estimated_size)}"
            )
            if plan.profile.tradeoffs:
                show_info(f"   Coste: {plan.profile.tradeoffs}")
        else:
            show_warning(f"{plan.media_file.path.name}: omitido ({plan.skip_reason})")
    return executable_plans
