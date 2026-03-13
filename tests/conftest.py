import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CLIBASEAPP_SRC = REPO_ROOT / "clibaseapp" / "src"
MEDIA_TOOLS_ROOT = REPO_ROOT / "media-tools"

for import_path in (MEDIA_TOOLS_ROOT, CLIBASEAPP_SRC):
    import_path_str = str(import_path)
    if import_path_str not in sys.path:
        sys.path.insert(0, import_path_str)

from models.schemas import MediaFile

@pytest.fixture
def mock_mkvmerge_output():
    """Provides a sample valid JSON output from mkvmerge -J."""
    return {
        "container": {"type": "Matroska"},
        "tracks": [
            {
                "codec": "MPEG-4p10/AVC/H.264",
                "id": 0,
                "type": "video",
                "properties": {
                    "language": "und",
                    "default_track": True,
                    "forced_track": False
                }
            },
            {
                "codec": "AAC",
                "id": 1,
                "type": "audio",
                "properties": {
                    "language": "spa",
                    "audio_channels": 2,
                    "default_track": True,
                    "forced_track": False
                }
            },
            {
                "codec": "AC-3",
                "id": 2,
                "type": "audio",
                "properties": {
                    "language": "eng",
                    "audio_channels": 6,
                    "default_track": False,
                    "forced_track": False
                }
            },
            {
                "codec": "SubRip/SRT",
                "id": 3,
                "type": "subtitles",
                "properties": {
                    "language": "spa",
                    "default_track": False,
                    "forced_track": False
                }
            }
        ]
    }

@pytest.fixture
def sample_media_files():
    """Provides a list of fully constructed MediaFile objects for testing AuditService."""
    from models.schemas import Track
    return [
        MediaFile(
            path=Path("/movies/pelicula1.mkv"),
            container="Matroska",
            tracks=[
                Track(id=0, codec="H.264", language="und", type="video"),
                Track(id=1, codec="AAC", language="spa", type="audio", channels=2),
                Track(id=2, codec="SRT", language="spa", type="subtitles"),
            ]
        ),
        MediaFile(
            path=Path("/movies/pelicula2.mkv"),
            container="Matroska",
            tracks=[
                Track(id=0, codec="HEVC", language="und", type="video"),
                Track(id=1, codec="AC-3", language="eng", type="audio", channels=6),
            ]
        ),
        MediaFile(
            path=Path("/movies/pelicula3.mkv"),
            container="Matroska",
            tracks=[
                Track(id=0, codec="H.264", language="und", type="video"),
                Track(id=1, codec="AAC", language="spa", type="audio", channels=2),
                Track(id=2, codec="AAC", language="spa", type="audio", channels=2, name="Commentary"),
                Track(id=3, codec="SRT", language="spa", type="subtitles"),
                Track(id=4, codec="SRT", language="eng", type="subtitles"),
            ]
        )
    ]
