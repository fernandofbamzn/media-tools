"""
Errores personalizados de la aplicación.
"""


class MediaToolsError(Exception):
    """Error base de la aplicación."""


class MediaPermissionError(MediaToolsError):
    """Error de permisos al acceder a rutas o archivos multimedia."""


class BinaryMissingError(MediaToolsError):
    """Falta una dependencia binaria del sistema."""


class ExternalToolExecutionError(MediaToolsError):
    """Fallo al ejecutar una herramienta externa con retorno no-cero."""


class InvalidMediaMetadataError(MediaToolsError):
    """La metadata devuelta por la herramienta externa no es JSON válido."""


class ConfigurationError(MediaToolsError):
    """Error de configuración inválida."""


# Alias de compatibilidad hacia atrás.
PermissionError = MediaPermissionError
BinaryMissing = BinaryMissingError

class DependencyInstallationError(MediaToolsError):
    """Fallo al instalar dependencias de Python mediante pip."""

