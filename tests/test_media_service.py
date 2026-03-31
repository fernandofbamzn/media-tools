from pathlib import Path
from unittest.mock import Mock

from clibaseapp.models import BrowseResult
from models.schemas import ActionType, AuditReport, CleanPlan, MediaFile, OptimizationProfile, OptimizeOutcome, Track, TrackAction
from services.media_service import CleanResult, MediaService


def test_audit_cancelled_selection() -> None:
    service = MediaService()

    result = service.audit(None)

    assert result.cancelled is True
    assert result.report is None
    assert result.scanned_files == 0


def test_audit_without_files() -> None:
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
    service = MediaService()
    plans = [
        CleanPlan(media_file=MediaFile(path=tmp_path / "one.mkv", container="Matroska"), track_actions=[], keep_languages=["spa"]),
        CleanPlan(media_file=MediaFile(path=tmp_path / "two.mkv", container="Matroska"), track_actions=[], keep_languages=["spa"]),
        CleanPlan(media_file=MediaFile(path=tmp_path / "three.mkv", container="Matroska"), track_actions=[], keep_languages=["spa"]),
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


def test_build_optimize_plans_from_media_files_returns_supported_and_skipped(tmp_path: Path) -> None:
    service = MediaService()
    supported = MediaFile(
        path=tmp_path / "one.mkv",
        container="Matroska",
        tracks=[Track(id=0, codec="H.264", language="und", type="video")],
    )
    skipped = MediaFile(
        path=tmp_path / "two.mkv",
        container="Matroska",
        tracks=[
            Track(id=0, codec="H.264", language="und", type="video"),
            Track(id=1, codec="H.264", language="und", type="video"),
        ],
    )
    supported.path.write_bytes(b"x" * 100)
    skipped.path.write_bytes(b"x" * 100)

    plans = service.build_optimize_plans_from_media_files([supported, skipped])

    assert len(plans) == 2
    assert plans[0].can_optimize is True
    assert plans[1].can_optimize is False


def test_execute_optimize_plans_collects_outputs_skips_and_failures(tmp_path: Path) -> None:
    service = MediaService()
    plans = [
        Mock(can_optimize=True, media_file=Mock(path=tmp_path / "one.mkv")),
        Mock(can_optimize=False, media_file=Mock(path=tmp_path / "two.mkv")),
        Mock(can_optimize=True, media_file=Mock(path=tmp_path / "three.mkv")),
    ]
    output = OptimizeOutcome(
        input_path=tmp_path / "one.mkv",
        output_path=tmp_path / "one.optimized.mkv",
        original_size=1000,
        optimized_size=600,
        bytes_saved=400,
    )
    service.execute_optimize_plan = Mock(side_effect=[output, RuntimeError("boom")])

    result = service.execute_optimize_plans(plans)

    assert result.files_processed == 3
    assert result.files_optimized == 1
    assert result.files_skipped == 1
    assert result.files_with_errors == 1
    assert result.bytes_saved == 400
    assert result.outputs == [output]
    assert result.skipped == [plans[1]]


def test_build_optimize_plans_from_media_files_accepts_dynamic_profile(tmp_path: Path) -> None:
    service = MediaService()
    media_file = MediaFile(
        path=tmp_path / "one.mkv",
        container="Matroska",
        tracks=[Track(id=0, codec="H.264", language="und", type="video")],
    )
    media_file.path.write_bytes(b"x" * 100)
    profile = OptimizationProfile(
        id="custom-balanced",
        title="Custom",
        video_codec="libx265",
        audio_codec="aac",
        ffmpeg_args=["-c:v", "libx265"],
        estimated_ratio=0.5,
    )
    service.optimize_service.build_plans = Mock(return_value=["plan"])

    plans = service.build_optimize_plans_from_media_files([media_file], profile=profile)

    assert plans == ["plan"]
    service.optimize_service.build_plans.assert_called_once_with([media_file], profile)
