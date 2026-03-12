"""
Visor interno de documentación Markdown.
"""

from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown

console = Console()


def show_docs():
    """Muestra la documentación integrada."""

    files = list(Path(".").glob("*.md")) + list(Path("docs").glob("*.md"))

    if not files:
        console.print("[yellow]No hay documentación disponible[/]")
        return

    for f in files:

        console.print(f"\n[cyan]{f}[/]\n")

        with open(f) as md:

            console.print(Markdown(md.read()))
