"""
Definición de estilos para la interfaz visual.
"""

from rich.theme import Theme

# Tema personalizado para la aplicación (usado por Console)
APP_THEME = Theme(
    {
        "info": "cyan",
        "success": "bold green",
        "warning": "bold yellow",
        "error": "bold red",
        "header": "bold cyan",
        "breadcrumb": "dim cyan",
    }
)
