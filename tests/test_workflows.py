from pathlib import Path
from unittest.mock import Mock

from clibaseapp import ConfigManager
from clibaseapp.models import BrowseResult
from models.schemas import ActionType, CleanPlan, MediaFile, Track, TrackAction
from services.media_service import CleanFailure, CleanResult
from ui import workflows


def _build_plan(tmp_path: Path, *, remove_audio: bool) -> CleanPlan:
    media_file = MediaFile(
        path=tmp_path / "movie.mkv",
        container="Matroska",
        tracks=[
            Track(id=0, codec="H.264", language="und", type="video"),
            Track(id=1, codec="AAC", language="spa", type="audio"),
        ],
    )
    track_actions = [
        TrackAction(track=media_file.tracks[0], action=ActionType.KEEP),
        TrackAction(
            track=media_file.tracks[1],
            action=ActionType.REMOVE if remove_audio else ActionType.KEEP,
        ),
    ]
    return CleanPlan(media_file=media_file, track_actions=track_actions, keep_languages=["spa"])


def _build_config(tmp_path: Path) -> ConfigManager:
    config = ConfigManager(
        app_name="media-tools-tests",
        default_config={"media_root": str(tmp_path), "keep_languages": ["spa", "eng"]},
    )
    config.update("media_root", str(tmp_path))
    config.update("keep_languages", ["spa", "eng"])
    return config


def test_run_clean_workflow_cancels_on_language_prompt(monkeypatch, tmp_path: Path) -> None:
    """Prueba la cancelación temprana cuando se aborta el input inicial."""

    service = Mock()
    config = _build_config(tmp_path)
    text_prompt = Mock()
    text_prompt.ask.return_value = None
    browse_media = Mock()

    monkeypatch.setattr(workflows.questionary, "text", Mock(return_value=text_prompt))
    monkeypatch.setattr(workflows, "browse_media", browse_media)

    workflows.run_clean_workflow(service, config)

    browse_media.assert_not_called()
    service.build_clean_plans.assert_not_called()


def test_run_clean_workflow_handles_browse_cancel(monkeypatch, tmp_path: Path) -> None:
    """Prueba que se informa la cancelación al abortar la navegación."""

    service = Mock()
    config = _build_config(tmp_path)
    text_prompt = Mock()
    text_prompt.ask.return_value = ""
    show_warning = Mock()

    monkeypatch.setattr(workflows.questionary, "text", Mock(return_value=text_prompt))
    monkeypatch.setattr(workflows, "browse_media", Mock(return_value=None))
    monkeypatch.setattr(workflows, "show_warning", show_warning)

    workflows.run_clean_workflow(service, config)

    show_warning.assert_called_with("Selección cancelada.")
    service.build_clean_plans.assert_not_called()


def test_run_clean_workflow_warns_when_no_files_found(monkeypatch, tmp_path: Path) -> None:
    """Prueba que el workflow corta si no hay planes para la selección."""

    service = Mock()
    config = _build_config(tmp_path)
    selection = BrowseResult(selected_path=tmp_path, selection_type="directory")
    text_prompt = Mock()
    text_prompt.ask.return_value = ""
    show_warning = Mock()

    monkeypatch.setattr(workflows.questionary, "text", Mock(return_value=text_prompt))
    monkeypatch.setattr(workflows, "browse_media", Mock(return_value=selection))
    monkeypatch.setattr(workflows, "show_warning", show_warning)
    service.build_clean_plans.return_value = []

    workflows.run_clean_workflow(service, config)

    show_warning.assert_called_with("No se encontraron archivos multimedia para limpiar.")


def test_run_clean_workflow_reports_when_nothing_to_remove(monkeypatch, tmp_path: Path) -> None:
    """Prueba que se informa cuando todos los planes ya están limpios."""

    service = Mock()
    config = _build_config(tmp_path)
    selection = BrowseResult(selected_path=tmp_path, selection_type="directory")
    plan = _build_plan(tmp_path, remove_audio=False)
    text_prompt = Mock()
    text_prompt.ask.return_value = ""
    show_success = Mock()

    monkeypatch.setattr(workflows.questionary, "text", Mock(return_value=text_prompt))
    monkeypatch.setattr(workflows, "browse_media", Mock(return_value=selection))
    monkeypatch.setattr(workflows, "ask_global_clean_plans", Mock(return_value=[plan]))
    monkeypatch.setattr(workflows, "show_success", show_success)
    service.build_clean_plans.return_value = [plan]

    workflows.run_clean_workflow(service, config)

    show_success.assert_called_with("Los archivos ya cumplen con la selección. Nada que borrar.")


def test_run_clean_workflow_stops_when_confirmation_is_rejected(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """Prueba que la ejecución no arranca sin confirmación destructiva."""

    service = Mock()
    config = _build_config(tmp_path)
    selection = BrowseResult(selected_path=tmp_path, selection_type="directory")
    plan = _build_plan(tmp_path, remove_audio=True)
    text_prompt = Mock()
    text_prompt.ask.return_value = ""
    confirm_prompt = Mock()
    confirm_prompt.ask.return_value = False
    show_warning = Mock()
    execute_with_progress = Mock()

    monkeypatch.setattr(workflows.questionary, "text", Mock(return_value=text_prompt))
    monkeypatch.setattr(workflows.questionary, "confirm", Mock(return_value=confirm_prompt))
    monkeypatch.setattr(workflows, "browse_media", Mock(return_value=selection))
    monkeypatch.setattr(workflows, "ask_global_clean_plans", Mock(return_value=[plan]))
    monkeypatch.setattr(workflows, "show_warning", show_warning)
    monkeypatch.setattr(workflows, "_execute_plans_with_progress", execute_with_progress)
    service.build_clean_plans.return_value = [plan]

    workflows.run_clean_workflow(service, config)

    execute_with_progress.assert_not_called()
    assert any(call.args == ("Cancelado.",) for call in show_warning.call_args_list)


def test_run_clean_workflow_renders_partial_failures(monkeypatch, tmp_path: Path) -> None:
    """Prueba la ruta con errores parciales durante la limpieza."""

    service = Mock()
    config = _build_config(tmp_path)
    selection = BrowseResult(selected_path=tmp_path, selection_type="directory")
    plan = _build_plan(tmp_path, remove_audio=True)
    text_prompt = Mock()
    text_prompt.ask.return_value = ""
    confirm_prompt = Mock()
    confirm_prompt.ask.return_value = True
    render_clean_result = Mock()
    result = CleanResult(
        files_processed=1,
        files_with_errors=1,
        bytes_saved=0,
        failures=[CleanFailure(file_path=plan.media_file.path, message="boom")],
    )

    monkeypatch.setattr(workflows.questionary, "text", Mock(return_value=text_prompt))
    monkeypatch.setattr(workflows.questionary, "confirm", Mock(return_value=confirm_prompt))
    monkeypatch.setattr(workflows, "browse_media", Mock(return_value=selection))
    monkeypatch.setattr(workflows, "ask_global_clean_plans", Mock(return_value=[plan]))
    monkeypatch.setattr(workflows, "_execute_plans_with_progress", Mock(return_value=result))
    monkeypatch.setattr(workflows, "_render_clean_result", render_clean_result)
    service.build_clean_plans.return_value = [plan]

    workflows.run_clean_workflow(service, config)

    render_clean_result.assert_called_once_with(result)
