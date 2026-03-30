from pathlib import Path

from models.schemas import MediaFile, Track
from services.optimize_service import DEFAULT_OPTIMIZATION_PROFILES, OptimizeService


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
