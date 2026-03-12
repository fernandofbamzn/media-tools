"""
Errores personalizados de la aplicación.
"""


class MediaToolsError(Exception):
    """Error base de la aplicación."""


class PermissionError(MediaToolsError):
    """Error de permisos."""


class BinaryMissing(MediaToolsError):
    """Falta una dependencia del sistema."""
