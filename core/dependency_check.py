import importlib
import subprocess
import sys

import questionary
from rich.console import Console

console = Console()

REQUIRED_PACKAGES = [
    "rich",
    "questionary",
    "typer",
    "pydantic",
]


def missing_packages():
    """Detecta dependencias faltantes."""
    missing = []

    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg)

    return missing


def install_packages(packages):
    """Instala paquetes usando el pip del entorno actual."""
    subprocess.run(
        [sys.executable, "-m", "pip", "install"] + packages,
        check=True,
    )


def check_and_install():
    """
    Comprueba dependencias del proyecto.
    Solo interactúa si falta algo.
    """

    missing = missing_packages()

    if not missing:
        return

    console.print("\n[cyan]Dependencias faltantes detectadas:[/]\n")

    for pkg in missing:
        console.print(f" • {pkg}")

    confirm = questionary.confirm(
        "¿Instalarlas ahora?",
        default=True
    ).ask()

    if confirm:
        install_packages(missing)
        console.print("[green]Dependencias instaladas correctamente.[/]\n")
    else:
        console.print("[yellow]El programa puede no funcionar correctamente.[/]\n")
