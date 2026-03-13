import ast
from pathlib import Path


def test_media_service_has_no_ui_dependencies() -> None:
    """Prueba que MediaService no importa dependencias de interfaz."""

    service_file = Path(__file__).resolve().parents[1] / "services" / "media_service.py"
    module = ast.parse(service_file.read_text(encoding="utf-8"))

    forbidden_modules = {"questionary", "rich"}
    forbidden_names = {
        "BrowserMenu",
        "clear_screen",
        "console",
        "fmt",
        "show_error",
        "show_header",
        "show_info",
        "show_success",
        "show_warning",
    }

    for node in module.body:
        if isinstance(node, ast.Import):
            imported_modules = {alias.name.split(".")[0] for alias in node.names}
            assert imported_modules.isdisjoint(forbidden_modules)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_modules
            imported_names = {alias.name for alias in node.names}
            assert imported_names.isdisjoint(forbidden_names)
