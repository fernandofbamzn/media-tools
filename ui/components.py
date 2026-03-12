"""
Componentes visuales reutilizables.
"""

from typing import Dict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ui.theme import APP_THEME

console = Console(theme=APP_THEME)


def show_header(title: str, breadcrumb: str = "") -> None:
    """Renderiza encabezado principal con breadcrumb."""
    if breadcrumb:
        console.print(f"[breadcrumb]{breadcrumb}[/breadcrumb]")
    console.print(Panel(f"[header]{title}[/header]", border_style="cyan"))


def show_info(text: str) -> None:
    """Mensaje informativo."""
    console.print(f"[info]ℹ {text}[/info]")


def show_success(text: str) -> None:
    """Mensaje de éxito."""
    console.print(f"[success]✔ {text}[/success]")


def show_warning(text: str) -> None:
    """Mensaje de advertencia."""
    console.print(f"[warning]⚠ {text}[/warning]")


def show_error(text: str) -> None:
    """Mensaje de error."""
    console.print(f"[error]✖ {text}[/error]")


def dict_table(title: str, values: Dict[str, int], key_label: str, value_label: str) -> Table:
    """Construye una tabla Rich a partir de un diccionario."""
    table = Table(title=title, show_lines=False)
    table.add_column(key_label, style="cyan")
    table.add_column(value_label, justify="right", style="green")

    for key, value in sorted(values.items(), key=lambda x: (-x[1], x[0])):
        table.add_row(str(key), str(value))

    return table
