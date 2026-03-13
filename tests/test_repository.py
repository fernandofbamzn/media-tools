import json
import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

from clibaseapp.exceptions import BinaryMissingError, ExternalToolError
from core.exceptions import InvalidMediaMetadataError
from data.repository import MediaRepository
from models.schemas import ActionType, CleanPlan, MediaFile, Track, TrackAction


def test_analyze_many_delegates_to_analyze_file(tmp_path: Path) -> None:
    """Prueba que analyze_many procesa todos los archivos solicitados."""

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
    """Prueba el análisis exitoso de un archivo usando mkvmerge."""

    repo = MediaRepository()
    test_file = tmp_path / "test.mkv"

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


def test_analyze_file_binary_missing(monkeypatch, tmp_path: Path) -> None:
    """Prueba el comportamiento cuando mkvmerge no está en PATH."""

    repo = MediaRepository()
    test_file = tmp_path / "test.mkv"

    def raise_missing(*args, **kwargs):
        raise FileNotFoundError("missing mkvmerge")

    monkeypatch.setattr(subprocess, "run", raise_missing)

    with pytest.raises(BinaryMissingError, match="No se encontró 'mkvmerge'"):
        repo.analyze_file(test_file)


def test_analyze_file_execution_error(monkeypatch, tmp_path: Path) -> None:
    """Prueba un código de salida diferente de 0 de mkvmerge."""

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
    """Prueba la respuesta cuando mkvmerge devuelve un JSON inválido."""

    repo = MediaRepository()
    test_file = tmp_path / "test.mkv"

    monkeypatch.setattr(
        subprocess,
        "run",
        Mock(return_value=Mock(stdout="Not a JSON output", returncode=0)),
    )

    with pytest.raises(InvalidMediaMetadataError, match="JSON inválido de mkvmerge"):
        repo.analyze_file(test_file)


def test_execute_remux_success(monkeypatch, tmp_path: Path) -> None:
    """Prueba que execute_remux genera el comando esperado y reemplaza el archivo."""

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
    """Prueba que el archivo temporal se elimina si mkvmerge falla."""

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
