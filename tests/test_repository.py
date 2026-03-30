import json
import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

from clibaseapp.exceptions import BinaryMissingError, ExternalToolError
from core.exceptions import InvalidMediaMetadataError
from data.repository import MediaRepository
from models.schemas import ActionType, CleanPlan, MediaFile, OptimizationProfile, OptimizePlan, Track, TrackAction


def test_analyze_many_delegates_to_analyze_file(tmp_path: Path) -> None:
    repo = MediaRepository()
    files = [tmp_path / "one.mkv", tmp_path / "two.mkv"]
    analyzed = [
        MediaFile(path=files[0], container="Matroska"),
        MediaFile(path=files[1], container="Matroska"),
    ]
    repo.analyze_file = Mock(side_effect=analyzed)

    result = repo.analyze_many(files)

    assert result == analyzed
    assert repo.analyze_file.call_count == 2


def test_analyze_file_success(monkeypatch, mock_mkvmerge_output: dict, tmp_path: Path) -> None:
    repo = MediaRepository()
    test_file = tmp_path / "test.mkv"
    repo._run_ffprobe = Mock(
        return_value=[
            {"codec_type": "video", "bit_rate": "1500000"},
            {"codec_type": "audio", "bit_rate": "192000", "tags": {"title": "Castellano", "language": "es-ES"}},
            {"codec_type": "audio", "bit_rate": "384000", "tags": {"title": "English 5.1", "language": "en"}},
            {"codec_type": "subtitle", "tags": {"title": "Forzados", "language": "es-ES"}},
        ]
    )

    monkeypatch.setattr(
        subprocess,
        "run",
        Mock(return_value=Mock(stdout=json.dumps(mock_mkvmerge_output), returncode=0)),
    )

    media = repo.analyze_file(test_file)

    assert isinstance(media, MediaFile)
    assert media.container == "Matroska"
    assert len(media.tracks) == 4
    assert len(media.video_tracks) == 1
    assert len(media.audio_tracks) == 2
    assert len(media.subtitle_tracks) == 1

    audio_spa = media.audio_tracks[0]
    assert audio_spa.language == "spa"
    assert audio_spa.channels == 2
    assert audio_spa.codec == "AAC"
    assert audio_spa.track_name == "Castellano"
    assert audio_spa.language_ietf == "es-ES"
    assert audio_spa.bitrate == 192000


def test_analyze_file_binary_missing(monkeypatch, tmp_path: Path) -> None:
    repo = MediaRepository()
    test_file = tmp_path / "test.mkv"

    def raise_missing(*args, **kwargs):
        raise FileNotFoundError("missing mkvmerge")

    monkeypatch.setattr(subprocess, "run", raise_missing)

    with pytest.raises(BinaryMissingError, match="No se encontro 'mkvmerge'"):
        repo.analyze_file(test_file)


def test_analyze_file_execution_error(monkeypatch, tmp_path: Path) -> None:
    repo = MediaRepository()
    test_file = tmp_path / "test.mkv"

    def raise_called_process_error(*args, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=2,
            cmd=["mkvmerge"],
            stderr="File format not recognized",
        )

    monkeypatch.setattr(subprocess, "run", raise_called_process_error)

    with pytest.raises(ExternalToolError, match="mkvmerge error para 'test.mkv'"):
        repo.analyze_file(test_file)


def test_analyze_file_invalid_json(monkeypatch, tmp_path: Path) -> None:
    repo = MediaRepository()
    test_file = tmp_path / "test.mkv"

    monkeypatch.setattr(
        subprocess,
        "run",
        Mock(return_value=Mock(stdout="Not a JSON output", returncode=0)),
    )

    with pytest.raises(InvalidMediaMetadataError, match="JSON invalido de mkvmerge"):
        repo.analyze_file(test_file)


def test_execute_remux_success(monkeypatch, tmp_path: Path) -> None:
    repo = MediaRepository()
    input_path = tmp_path / "movie.mkv"
    input_path.write_bytes(b"original")
    temp_path = tmp_path / "movie_tmp.mkv"

    media_file = MediaFile(
        path=input_path,
        container="Matroska",
        tracks=[
            Track(id=0, codec="H.264", language="und", type="video"),
            Track(id=1, codec="AAC", language="spa", type="audio"),
            Track(id=2, codec="SRT", language="spa", type="subtitles"),
        ],
    )
    plan = CleanPlan(
        media_file=media_file,
        track_actions=[
            TrackAction(track=media_file.tracks[0], action=ActionType.KEEP),
            TrackAction(track=media_file.tracks[1], action=ActionType.KEEP),
            TrackAction(track=media_file.tracks[2], action=ActionType.KEEP),
        ],
        keep_languages=["spa"],
    )

    def run_side_effect(command: list[str], capture_output: bool, text: bool, check: bool) -> None:
        assert command == [
            "mkvmerge",
            "-o",
            str(temp_path),
            "--audio-tracks",
            "1",
            "--subtitle-tracks",
            "2",
            str(input_path),
        ]
        temp_path.write_bytes(b"remuxed")

    monkeypatch.setattr(subprocess, "run", run_side_effect)

    repo.execute_remux(plan)

    assert input_path.read_bytes() == b"remuxed"
    assert not temp_path.exists()


def test_execute_remux_cleans_temp_file_on_command_error(monkeypatch, tmp_path: Path) -> None:
    repo = MediaRepository()
    input_path = tmp_path / "movie.mkv"
    input_path.write_bytes(b"original")
    temp_path = tmp_path / "movie_tmp.mkv"

    media_file = MediaFile(
        path=input_path,
        container="Matroska",
        tracks=[Track(id=0, codec="H.264", language="und", type="video")],
    )
    plan = CleanPlan(
        media_file=media_file,
        track_actions=[TrackAction(track=media_file.tracks[0], action=ActionType.KEEP)],
        keep_languages=["spa"],
    )

    def run_side_effect(command: list[str], capture_output: bool, text: bool, check: bool) -> None:
        temp_path.write_bytes(b"partial")
        raise subprocess.CalledProcessError(returncode=2, cmd=command, stderr="boom")

    monkeypatch.setattr(subprocess, "run", run_side_effect)

    with pytest.raises(ExternalToolError, match="Error al limpiar 'movie.mkv'. boom"):
        repo.execute_remux(plan)

    assert input_path.exists()
    assert not temp_path.exists()


def test_execute_optimization_success(monkeypatch, tmp_path: Path) -> None:
    repo = MediaRepository()
    input_path = tmp_path / "movie.mkv"
    input_path.write_bytes(b"x" * 1000)
    output_path = tmp_path / "movie.optimized.mkv"
    temp_output = tmp_path / "movie.optimized.tmp.mkv"

    media_file = MediaFile(
        path=input_path,
        container="Matroska",
        tracks=[Track(id=0, codec="H.264", language="und", type="video")],
    )
    profile = OptimizationProfile(
        id="h265-opus",
        title="H.265/Opus ahorro",
        video_codec="libx265",
        audio_codec="libopus",
        ffmpeg_args=["-c:v", "libx265", "-c:a", "libopus", "-c:s", "copy"],
        estimated_ratio=0.6,
    )
    plan = OptimizePlan(
        media_file=media_file,
        profile=profile,
        output_path=output_path,
        original_size=1000,
        estimated_size=600,
        can_optimize=True,
    )

    def run_side_effect(command: list[str], capture_output: bool, text: bool, check: bool) -> None:
        assert command[:8] == ["ffmpeg", "-y", "-i", str(input_path), "-map", "0", "-map_metadata", "0"]
        temp_output.write_bytes(b"x" * 600)

    monkeypatch.setattr(subprocess, "run", run_side_effect)

    outcome = repo.execute_optimization(plan)

    assert outcome.output_path == output_path
    assert outcome.bytes_saved == 400
    assert output_path.exists()


def test_replace_original_with_output_replaces_original(tmp_path: Path) -> None:
    repo = MediaRepository()
    input_path = tmp_path / "movie.mkv"
    output_path = tmp_path / "movie.optimized.mkv"
    input_path.write_bytes(b"old")
    output_path.write_bytes(b"new")

    repo.replace_original_with_output(
        Mock(
            input_path=input_path,
            output_path=output_path,
        )
    )

    assert input_path.read_bytes() == b"new"
    assert not output_path.exists()
