import json
import subprocess
from pathlib import Path
import pytest
from pytest_mock import MockerFixture

from core.exceptions import (
    BinaryMissingError,
    ExternalToolExecutionError,
    InvalidMediaMetadataError,
    MediaPermissionError,
)
from data.repository import MediaRepository
from models.schemas import MediaFile

def test_scan_finds_valid_extensions(tmp_path: Path):
    """Prueba que el escaneo solo devuelve archivos con extensiones esperadas."""
    repo = MediaRepository()
    
    (tmp_path / "video1.mkv").touch()
    (tmp_path / "video2.mp4").touch()
    (tmp_path / "video3.m4v").touch()
    (tmp_path / "documento.txt").touch()
    (tmp_path / "subcarpeta").mkdir()
    (tmp_path / "subcarpeta" / "video4.mkv").touch()

    files = repo.scan(tmp_path)
    
    assert len(files) == 4
    file_names = {f.name for f in files}
    assert file_names == {"video1.mkv", "video2.mp4", "video3.m4v", "video4.mkv"}

def test_scan_permission_error(mocker: MockerFixture, tmp_path: Path):
    """Prueba que un error de permisos en rglob lanza la excepción correcta."""
    repo = MediaRepository()

    # Mock Path.rglob as raising PermissionError
    mocker.patch.object(Path, 'rglob', side_effect=PermissionError("Access Denied"))

    with pytest.raises(MediaPermissionError, match="Permiso denegado al escanear la ruta"):
        repo.scan(tmp_path)

def test_analyze_file_success(mocker: MockerFixture, mock_mkvmerge_output: dict, tmp_path: Path):
    """Prueba el análisis exitoso de un archivo usando mkvmerge."""
    repo = MediaRepository()
    test_file = tmp_path / "test.mkv"

    mock_run = mocker.patch('subprocess.run')
    mock_run.return_value.stdout = json.dumps(mock_mkvmerge_output)
    mock_run.return_value.returncode = 0

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

def test_analyze_file_binary_missing(mocker: MockerFixture, tmp_path: Path):
    """Prueba comportamiento cuando el binario mkvmerge no está en PATH."""
    repo = MediaRepository()
    test_file = tmp_path / "test.mkv"

    mocker.patch('subprocess.run', side_effect=FileNotFoundError("No such file or directory: 'mkvmerge'"))

    with pytest.raises(BinaryMissingError, match="No se encontró 'mkvmerge'"):
        repo.analyze_file(test_file)

def test_analyze_file_execution_error(mocker: MockerFixture, tmp_path: Path):
    """Prueba un código de salida diferente de 0 de mkvmerge."""
    repo = MediaRepository()
    test_file = tmp_path / "test.mkv"

    mock_run = mocker.patch('subprocess.run', side_effect=subprocess.CalledProcessError(
        returncode=2, cmd=["mkvmerge"], stderr="File format not recognized"
    ))

    with pytest.raises(ExternalToolExecutionError, match="mkvmerge devolvió código 2"):
        repo.analyze_file(test_file)

def test_analyze_file_invalid_json(mocker: MockerFixture, tmp_path: Path):
    """Prueba la respuesta cuando mkvmerge devuelve contenido que no es JSON."""
    repo = MediaRepository()
    test_file = tmp_path / "test.mkv"

    mock_run = mocker.patch('subprocess.run')
    mock_run.return_value.stdout = "Not a JSON output"
    mock_run.return_value.returncode = 0

    with pytest.raises(InvalidMediaMetadataError, match="Salida JSON inválida de mkvmerge"):
        repo.analyze_file(test_file)
