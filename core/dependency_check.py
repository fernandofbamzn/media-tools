import importlib
import subprocess
import sys
from types import ModuleType
from typing import Optional, Sequence

from rich.console import Console

from core.exceptions import DependencyInstallationError

console = Console()

REQUIRED_PACKAGES = [
    "rich",
    "questionary",
    "typer",
    "pydantic",
]


def _load_optional_module(module_name: str) -> Optional[ModuleType]:
    """Carga un módulo opcional y devuelve None si no está disponible."""
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None


def missing_packages() -> list[str]:
    """Detecta dependencias faltantes."""
    missing: list[str] = []

    for pkg in REQUIRED_PACKAGES:
        if _load_optional_module(pkg) is None:
            missing.append(pkg)

    return missing


def install_packages(packages: Sequence[str]) -> None:
    """Instala paquetes usando el pip del entorno actual."""
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", *packages],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        stdout = (exc.stdout or "").strip()
        details = stderr or stdout or "Sin salida de error disponible."
        raise DependencyInstallationError(
            f"No se pudieron instalar dependencias ({', '.join(packages)}): {details}"
        ) from exc


def _ask_install_confirmation_with_questionary() -> Optional[bool]:
    """Solicita confirmación con questionary si está disponible."""
    questionary_module = _load_optional_module("questionary")

    if questionary_module is None:
        return None

    confirm = questionary_module.confirm(
        "¿Instalarlas ahora?",
        default=True,
    ).ask()
    return bool(confirm)


def check_and_install() -> None:
    """Comprueba dependencias del proyecto y gestiona su instalación."""
    missing = missing_packages()

    if not missing:
        return

    console.print("\n[cyan]Dependencias faltantes detectadas:[/]\n")
    for pkg in missing:
        console.print(f" • {pkg}")

    confirm = _ask_install_confirmation_with_questionary()
    if confirm is None:
        console.print(
            "\n[yellow]No se encontró 'questionary'. No se puede solicitar confirmación interactiva.[/]"
        )
        console.print(
            "[yellow]Instala las dependencias manualmente y vuelve a ejecutar el comando.[/]\n"
        )
        raise SystemExit(1)

    if not confirm:
        console.print("[yellow]Instalación cancelada por el usuario.[/]\n")
        raise SystemExit(1)

    try:
        install_packages(missing)
    except DependencyInstallationError as exc:
        console.print(f"[red]{exc}[/]\n")
        raise SystemExit(1) from exc

    console.print("[green]Dependencias instaladas correctamente.[/]\n")
