from pathlib import Path
from unittest.mock import Mock

from clibaseapp.models import BrowseResult
from models.schemas import ActionType, AuditReport, CleanPlan, MediaFile, Track, TrackAction
from services.media_service import CleanResult, MediaService


def test_audit_cancelled_selection() -> None:
    """Prueba que una selección cancelada devuelve un resumen cancelado."""

    service = MediaService()

    result = service.audit(None)

    assert result.cancelled is True
    assert result.report is None
    assert result.scanned_files == 0


def test_audit_without_files() -> None:
    """Prueba que una selección vacía no intenta analizar archivos."""

    service = MediaService()
    selection = BrowseResult(selected_path=Path("/library"), selection_type="directory")
    service._resolve_files = Mock(return_value=[])
    service.repo.analyze_many = Mock()

    result = service.audit(selection)

    assert result.cancelled is False
    assert result.report is None
    assert result.scanned_files == 0
    service.repo.analyze_many.assert_not_called()


def test_audit_builds_report_from_analyzed_files(sample_media_files) -> None:
    """Prueba que audit coordina repositorio y servicio de auditoría."""

    service = MediaService()
    selection = BrowseResult(selected_path=Path("/library"), selection_type="directory")
    report = AuditReport(
        total_files=3,
        audio_languages={},
        subtitle_languages={},
        video_codecs={},
        audio_codecs={},
        files_without_subtitles=0,
        files_without_spanish_audio=0,
        files_with_duplicate_candidate_audio=0,
        detailed_files=sample_media_files,
    )
    service._resolve_files = Mock(return_value=[Path("/library/movie.mkv")])
    service.repo.analyze_many = Mock(return_value=sample_media_files)
    service.audit_service.build_report = Mock(return_value=report)

    result = service.audit(selection)

    service.repo.analyze_many.assert_called_once()
    service.audit_service.build_report.assert_called_once_with(sample_media_files)
    assert result.report == report
    assert result.scanned_files == 1


def test_build_clean_plans_returns_plan_per_analyzed_file() -> None:
    """Prueba que build_clean_plans devuelve un plan por archivo analizado."""

    service = MediaService()
    selection = BrowseResult(selected_path=Path("/library"), selection_type="directory")
    media_file = MediaFile(
        path=Path("/library/movie.mkv"),
        container="Matroska",
        tracks=[Track(id=0, codec="H.264", language="und", type="video")],
    )
    plan = CleanPlan(
        media_file=media_file,
        track_actions=[TrackAction(track=media_file.tracks[0], action=ActionType.KEEP)],
        keep_languages=["spa"],
    )
    service._resolve_files = Mock(return_value=[media_file.path])
    service.repo.analyze_many = Mock(return_value=[media_file])
    service.clean_service.build_plan = Mock(return_value=plan)

    result = service.build_clean_plans(selection, ["spa"])

    assert result == [plan]
    service.clean_service.build_plan.assert_called_once_with(media_file, ["spa"])


def test_build_clean_plans_from_media_files_reuses_analysis() -> None:
    """Prueba que se pueden generar planes sin relanzar la auditoría."""

    service = MediaService()
    media_file = MediaFile(
        path=Path("/library/movie.mkv"),
        container="Matroska",
        tracks=[Track(id=0, codec="H.264", language="und", type="video")],
    )
    plan = CleanPlan(
        media_file=media_file,
        track_actions=[TrackAction(track=media_file.tracks[0], action=ActionType.KEEP)],
        keep_languages=["spa"],
    )
    service.clean_service.build_plan = Mock(return_value=plan)
    service.repo.analyze_many = Mock()

    result = service.build_clean_plans_from_media_files([media_file], ["spa"])

    assert result == [plan]
    service.clean_service.build_plan.assert_called_once_with(media_file, ["spa"])
    service.repo.analyze_many.assert_not_called()


def test_execute_clean_plans_collects_failures(tmp_path: Path) -> None:
    """Prueba que la ejecución agregada conserva bytes y errores."""

    service = MediaService()
    plans = [
        CleanPlan(
            media_file=MediaFile(path=tmp_path / "one.mkv", container="Matroska"),
            track_actions=[],
            keep_languages=["spa"],
        ),
        CleanPlan(
            media_file=MediaFile(path=tmp_path / "two.mkv", container="Matroska"),
            track_actions=[],
            keep_languages=["spa"],
        ),
        CleanPlan(
            media_file=MediaFile(path=tmp_path / "three.mkv", container="Matroska"),
            track_actions=[],
            keep_languages=["spa"],
        ),
    ]
    service.execute_clean_plan = Mock(side_effect=[120, RuntimeError("boom"), 30])

    result = service.execute_clean_plans(plans)

    assert isinstance(result, CleanResult)
    assert result.files_processed == 3
    assert result.files_with_errors == 1
    assert result.bytes_saved == 150
    assert len(result.failures) == 1
    assert result.failures[0].file_path == plans[1].media_file.path
    assert result.failures[0].message == "boom"
