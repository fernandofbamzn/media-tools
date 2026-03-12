"""
Excepciones personalizadas de media-tools.
Heredan de las excepciones base del framework clibaseapp.
"""

from clibaseapp.exceptions import CLIAppError


class MediaToolsError(CLIAppError):
    """Error base de la aplicación media-tools."""


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


class DependencyInstallationError(MediaToolsError):
    """Fallo al instalar dependencias de Python mediante pip."""
