from pathlib import Path

from models.schemas import MediaFile, Track
from services.optimize_service import CUSTOM_OPTIMIZATION_PROFILE, DEFAULT_OPTIMIZATION_PROFILES, OptimizeService


def test_build_plan_marks_multi_video_files_as_skipped(tmp_path: Path) -> None:
    service = OptimizeService()
    media_file = MediaFile(
        path=tmp_path / "movie.mkv",
        container="Matroska",
        tracks=[
            Track(id=0, codec="H.264", language="und", type="video"),
            Track(id=1, codec="H.264", language="und", type="video"),
        ],
    )
    media_file.path.write_bytes(b"x" * 1000)

    plan = service.build_plan(media_file, DEFAULT_OPTIMIZATION_PROFILES[0])

    assert plan.can_optimize is False
    assert "exactamente una pista de video" in plan.skip_reason


def test_build_plan_uses_optimized_mkv_output_and_estimated_ratio(tmp_path: Path) -> None:
    service = OptimizeService()
    media_file = MediaFile(
        path=tmp_path / "movie.mp4",
        container="QuickTime",
        tracks=[Track(id=0, codec="H.264", language="und", type="video")],
    )
    media_file.path.write_bytes(b"x" * 1000)

    plan = service.build_plan(media_file, DEFAULT_OPTIMIZATION_PROFILES[0])

    assert plan.can_optimize is True
    assert plan.output_path.name == "movie.optimized.mkv"
    assert 0 < plan.estimated_size < plan.original_size


def test_list_profiles_includes_guided_custom_profile() -> None:
    service = OptimizeService()

    profiles = service.list_profiles()

    assert profiles[-1] == CUSTOM_OPTIMIZATION_PROFILE


def test_build_custom_recommendations_uses_largest_supported_file(tmp_path: Path) -> None:
    service = OptimizeService()
    small = MediaFile(
        path=tmp_path / "small.mkv",
        container="Matroska",
        tracks=[Track(id=0, codec="H.264", language="und", type="video")],
    )
    large = MediaFile(
        path=tmp_path / "large.mkv",
        container="Matroska",
        tracks=[Track(id=0, codec="H.264", language="und", type="video")],
    )
    skipped = MediaFile(
        path=tmp_path / "skip.avi",
        container="AVI",
        tracks=[Track(id=0, codec="H.264", language="und", type="video")],
    )
    small.path.write_bytes(b"x" * 100)
    large.path.write_bytes(b"x" * 300)
    skipped.path.write_bytes(b"x" * 500)

    recommendations = service.build_custom_recommendations([small, large, skipped])

    assert recommendations is not None
    assert recommendations.reference_file == large
    assert recommendations.options
    assert recommendations.options[0].recommended is True


def test_build_custom_recommendations_prefers_softer_mode_for_hevc_sources(tmp_path: Path) -> None:
    service = OptimizeService()
    media_file = MediaFile(
        path=tmp_path / "movie.mkv",
        container="Matroska",
        tracks=[Track(id=0, codec="HEVC", language="und", type="video")],
    )
    media_file.path.write_bytes(b"x" * 1000)

    recommendations = service.build_custom_recommendations([media_file])

    assert recommendations is not None
    recommended = next(option for option in recommendations.options if option.recommended)
    assert recommended.profile.id == "custom-hevc-vaapi-quality"
