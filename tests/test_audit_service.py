import pytest
from data.repository import MediaRepository
from models.schemas import MediaFile
from services.audit_service import AuditService

def test_build_report_empty_list():
    """Prueba que el reporte se genera correctamente con una lista vacía."""
    service = AuditService()
    report = service.build_report([])

    assert report.total_files == 0
    assert report.files_without_subtitles == 0
    assert report.files_without_spanish_audio == 0
    assert report.files_with_duplicate_candidate_audio == 0
    assert report.audio_languages == {}
    assert report.subtitle_languages == {}
    assert report.video_codecs == {}
    assert report.audio_codecs == {}


def test_build_report_with_sample_files(sample_media_files):
    """Prueba el recuento de metadatos con archivos simulados."""
    service = AuditService()
    report = service.build_report(sample_media_files)

    assert report.total_files == 3
    
    # Archivos sin subtítulos: solo el segundo archivo carece de subtítulos
    assert report.files_without_subtitles == 1
    
    # Archivos sin audio en español: el segundo archivo solo tiene inglés
    assert report.files_without_spanish_audio == 1
    
    # Duplicados: el tercer archivo tiene dos pistas AAC en español
    assert report.files_with_duplicate_candidate_audio == 1

    # Agrupaciones:
    assert report.video_codecs == {"H.264": 2, "HEVC": 1}
    assert report.audio_languages == {"spa": 3, "eng": 1}
    assert report.subtitle_languages == {"spa": 2, "eng": 1}

def test_build_report_audio_languages_and_codecs(sample_media_files):
    service = AuditService()
    report = service.build_report(sample_media_files)
    
    assert report.audio_codecs == {"AAC": 3, "AC-3": 1}
