"""
Excepciones específicas de media-tools.
Las comunes (permisos, binarios, config, etc.) se heredan de clibaseapp.
"""

from clibaseapp.exceptions import CLIAppError


class MediaToolsError(CLIAppError):
    """Error base específico de media-tools."""


class InvalidMediaMetadataError(MediaToolsError):
    """La metadata devuelta por mkvmerge no es JSON válido."""
