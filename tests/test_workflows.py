from pathlib import Path
from unittest.mock import Mock

from clibaseapp import ConfigManager
from clibaseapp.models import BrowseResult
from models.schemas import ActionType, AuditReport, AuditSummary, CleanPlan, MediaFile, Track, TrackAction
from services.media_service import CleanFailure, CleanResult
from services.optimize_service import DEFAULT_OPTIMIZATION_PROFILES
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


def _build_audit_summary(tmp_path: Path) -> AuditSummary:
    media_file = MediaFile(
        path=tmp_path / "movie.mkv",
        container="Matroska",
        tracks=[
            Track(id=0, codec="H.264", language="und", type="video"),
            Track(id=1, codec="AAC", language="spa", type="audio"),
        ],
    )
    return AuditSummary(
        cancelled=False,
        selected_path=tmp_path,
        selection_type="directory",
        scanned_files=1,
        report=AuditReport(
            total_files=1,
            audio_languages={"spa": 1},
            subtitle_languages={},
            video_codecs={"H.264": 1},
            audio_codecs={"AAC": 1},
            files_without_subtitles=1,
            files_without_spanish_audio=0,
            files_with_duplicate_candidate_audio=0,
            detailed_files=[media_file],
        ),
    )


def test_run_clean_workflow_handles_browse_cancel(monkeypatch, tmp_path: Path) -> None:
    service = Mock()
    config = _build_config(tmp_path)
    show_warning = Mock()

    monkeypatch.setattr(workflows, "browse_media", Mock(return_value=None))
    monkeypatch.setattr(workflows, "show_warning", show_warning)

    workflows.run_clean_workflow(service, config)

    show_warning.assert_called_with("Seleccion cancelada.")
    service.audit.assert_not_called()


def test_run_clean_workflow_stops_when_audit_has_no_report(monkeypatch, tmp_path: Path) -> None:
    service = Mock()
    config = _build_config(tmp_path)
    selection = BrowseResult(selected_path=tmp_path, selection_type="directory")
    audit_summary = AuditSummary(
        cancelled=False,
        selected_path=tmp_path,
        selection_type="directory",
        scanned_files=0,
        report=None,
    )
    render_audit_summary = Mock()

    monkeypatch.setattr(workflows, "browse_media", Mock(return_value=selection))
    monkeypatch.setattr(workflows, "render_audit_summary", render_audit_summary)
    service.audit.return_value = audit_summary

    workflows.run_clean_workflow(service, config)

    render_audit_summary.assert_called_once_with(audit_summary)
    service.build_clean_plans_from_media_files.assert_not_called()


def test_run_clean_workflow_cancels_after_audit(monkeypatch, tmp_path: Path) -> None:
    service = Mock()
    config = _build_config(tmp_path)
    selection = BrowseResult(selected_path=tmp_path, selection_type="directory")
    audit_summary = _build_audit_summary(tmp_path)
    confirm_prompt = Mock()
    confirm_prompt.ask.return_value = False
    show_warning = Mock()

    monkeypatch.setattr(workflows.questionary, "confirm", Mock(return_value=confirm_prompt))
    monkeypatch.setattr(workflows, "browse_media", Mock(return_value=selection))
    monkeypatch.setattr(workflows, "show_warning", show_warning)
    service.audit.return_value = audit_summary

    workflows.run_clean_workflow(service, config)

    service.build_clean_plans_from_media_files.assert_not_called()
    assert any(call.args == ("Operacion cancelada.",) for call in show_warning.call_args_list)


def test_run_clean_workflow_cancels_on_language_prompt(monkeypatch, tmp_path: Path) -> None:
    service = Mock()
    config = _build_config(tmp_path)
    selection = BrowseResult(selected_path=tmp_path, selection_type="directory")
    audit_summary = _build_audit_summary(tmp_path)
    text_prompt = Mock()
    text_prompt.ask.return_value = None
    continue_prompt = Mock()
    continue_prompt.ask.return_value = True

    monkeypatch.setattr(workflows.questionary, "text", Mock(return_value=text_prompt))
    monkeypatch.setattr(workflows.questionary, "confirm", Mock(return_value=continue_prompt))
    monkeypatch.setattr(workflows, "browse_media", Mock(return_value=selection))
    service.audit.return_value = audit_summary

    workflows.run_clean_workflow(service, config)

    service.build_clean_plans_from_media_files.assert_not_called()


def test_run_clean_workflow_reports_when_nothing_to_remove(monkeypatch, tmp_path: Path) -> None:
    service = Mock()
    config = _build_config(tmp_path)
    selection = BrowseResult(selected_path=tmp_path, selection_type="directory")
    audit_summary = _build_audit_summary(tmp_path)
    plan = _build_plan(tmp_path, remove_audio=False)
    text_prompt = Mock()
    text_prompt.ask.return_value = ""
    continue_prompt = Mock()
    continue_prompt.ask.return_value = True
    show_success = Mock()

    monkeypatch.setattr(workflows.questionary, "text", Mock(return_value=text_prompt))
    monkeypatch.setattr(workflows.questionary, "confirm", Mock(return_value=continue_prompt))
    monkeypatch.setattr(workflows, "browse_media", Mock(return_value=selection))
    monkeypatch.setattr(workflows, "ask_global_clean_plans", Mock(return_value=[plan]))
    monkeypatch.setattr(workflows, "show_success", show_success)
    service.audit.return_value = audit_summary
    service.build_clean_plans_from_media_files.return_value = [plan]

    workflows.run_clean_workflow(service, config)

    service.build_clean_plans_from_media_files.assert_called_once_with(
        audit_summary.report.detailed_files,
        ["spa", "eng"],
    )
    show_success.assert_called_with("Los archivos ya cumplen con la seleccion. Nada que borrar.")


def test_run_clean_workflow_stops_when_confirmation_is_rejected(monkeypatch, tmp_path: Path) -> None:
    service = Mock()
    config = _build_config(tmp_path)
    selection = BrowseResult(selected_path=tmp_path, selection_type="directory")
    audit_summary = _build_audit_summary(tmp_path)
    plan = _build_plan(tmp_path, remove_audio=True)
    text_prompt = Mock()
    text_prompt.ask.return_value = ""
    continue_prompt = Mock()
    continue_prompt.ask.return_value = True
    apply_prompt = Mock()
    apply_prompt.ask.return_value = False
    execute_with_progress = Mock()
    show_warning = Mock()

    monkeypatch.setattr(
        workflows.questionary,
        "confirm",
        Mock(side_effect=[continue_prompt, apply_prompt]),
    )
    monkeypatch.setattr(workflows.questionary, "text", Mock(return_value=text_prompt))
    monkeypatch.setattr(workflows, "browse_media", Mock(return_value=selection))
    monkeypatch.setattr(workflows, "ask_global_clean_plans", Mock(return_value=[plan]))
    monkeypatch.setattr(workflows, "_execute_plans_with_progress", execute_with_progress)
    monkeypatch.setattr(workflows, "show_warning", show_warning)
    service.audit.return_value = audit_summary
    service.build_clean_plans_from_media_files.return_value = [plan]

    workflows.run_clean_workflow(service, config)

    execute_with_progress.assert_not_called()
    assert any(call.args == ("Cancelado.",) for call in show_warning.call_args_list)


def test_run_clean_workflow_renders_partial_failures(monkeypatch, tmp_path: Path) -> None:
    service = Mock()
    config = _build_config(tmp_path)
    selection = BrowseResult(selected_path=tmp_path, selection_type="directory")
    audit_summary = _build_audit_summary(tmp_path)
    plan = _build_plan(tmp_path, remove_audio=True)
    text_prompt = Mock()
    text_prompt.ask.return_value = ""
    continue_prompt = Mock()
    continue_prompt.ask.return_value = True
    apply_prompt = Mock()
    apply_prompt.ask.return_value = True
    render_clean_result = Mock()
    result = CleanResult(
        files_processed=1,
        files_with_errors=1,
        bytes_saved=0,
        failures=[CleanFailure(file_path=plan.media_file.path, message="boom")],
    )

    monkeypatch.setattr(
        workflows.questionary,
        "confirm",
        Mock(side_effect=[continue_prompt, apply_prompt]),
    )
    monkeypatch.setattr(workflows.questionary, "text", Mock(return_value=text_prompt))
    monkeypatch.setattr(workflows, "browse_media", Mock(return_value=selection))
    monkeypatch.setattr(workflows, "ask_global_clean_plans", Mock(return_value=[plan]))
    monkeypatch.setattr(workflows, "_execute_plans_with_progress", Mock(return_value=result))
    monkeypatch.setattr(workflows, "_render_clean_result", render_clean_result)
    service.audit.return_value = audit_summary
    service.build_clean_plans_from_media_files.return_value = [plan]

    workflows.run_clean_workflow(service, config)

    render_clean_result.assert_called_once_with(result)


def test_run_optimize_workflow_cancels_when_profile_prompt_returns_none(monkeypatch, tmp_path: Path) -> None:
    service = Mock()
    config = _build_config(tmp_path)
    selection = BrowseResult(selected_path=tmp_path, selection_type="directory")
    audit_summary = _build_audit_summary(tmp_path)
    show_warning = Mock()

    monkeypatch.setattr(workflows, "browse_media", Mock(return_value=selection))
    monkeypatch.setattr(workflows, "show_warning", show_warning)
    monkeypatch.setattr(workflows.questionary, "confirm", Mock(return_value=Mock(ask=Mock(return_value=True))))
    monkeypatch.setattr(workflows, "_ask_optimization_profile", Mock(return_value=None))
    service.audit.return_value = audit_summary

    workflows.run_optimize_workflow(service, config)

    show_warning.assert_called_with("Optimizacion cancelada.")


def test_run_optimize_workflow_executes_and_can_replace_originals(monkeypatch, tmp_path: Path) -> None:
    service = Mock()
    config = _build_config(tmp_path)
    selection = BrowseResult(selected_path=tmp_path, selection_type="directory")
    audit_summary = _build_audit_summary(tmp_path)
    profile = DEFAULT_OPTIMIZATION_PROFILES[0]
    plan = Mock(
        can_optimize=True,
        original_size=1000,
        estimated_size=600,
        media_file=Mock(path=tmp_path / "movie.mkv"),
        profile=profile,
    )
    result = Mock(
        outputs=[Mock()],
        skipped=[],
        failures=[],
        bytes_saved=400,
        files_optimized=1,
        files_skipped=0,
        files_with_errors=0,
    )

    continue_prompt = Mock()
    continue_prompt.ask.return_value = True
    execute_prompt = Mock()
    execute_prompt.ask.return_value = True
    replace_prompt = Mock()
    replace_prompt.ask.return_value = True

    monkeypatch.setattr(workflows, "browse_media", Mock(return_value=selection))
    monkeypatch.setattr(
        workflows.questionary,
        "confirm",
        Mock(side_effect=[continue_prompt, execute_prompt, replace_prompt]),
    )
    monkeypatch.setattr(workflows, "_ask_optimization_profile", Mock(return_value=profile))
    monkeypatch.setattr(workflows, "render_optimize_plan_summary", Mock(return_value=[plan]))
    monkeypatch.setattr(workflows, "_execute_optimize_plans_with_progress", Mock(return_value=result))
    monkeypatch.setattr(workflows, "_render_optimize_result", Mock())
    service.audit.return_value = audit_summary
    service.build_optimize_plans_from_media_files.return_value = [plan]
    service.replace_originals_with_optimized.return_value = []

    workflows.run_optimize_workflow(service, config)

    service.build_optimize_plans_from_media_files.assert_called_once_with(
        audit_summary.report.detailed_files,
        profile_id=profile.id,
    )
    service.replace_originals_with_optimized.assert_called_once_with(result.outputs)
