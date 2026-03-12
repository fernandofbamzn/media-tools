# **🛠 Guía Maestra para el Desarrollo de Aplicaciones CLI Profesionales**

Esta guía establece el estándar obligatorio y exhaustivo para la creación de herramientas de línea de comandos (CLI) en Python y Bash. El objetivo es construir aplicaciones que no solo sean visualmente impactantes, sino también robustas, automatizables, perfectamente documentadas y con una arquitectura de grado empresarial.

## **1\. Arquitectura de Software y Estructura Modular**

### **Separación de Capas (N-Tier CLI)**

Toda aplicación debe estar dividida en módulos para facilitar la edición y escalabilidad. No se permite el uso de un solo archivo.

* **Capa de Entrada (Entrypoint):** main.py \- Orquestación, manejo de argumentos y CLI Parser (Typer/Click).  
* **Capa de Presentación (UI/View):** ui/ o views/ \- Solo lógica de renderizado (Rich, tablas, colores, menús).  
* **Capa de Servicio (Business Logic):** services/ \- Lógica de negocio pura. No debe tener dependencias de la interfaz.  
* **Capa de Datos (Data Access):** data/ o repository/ \- Interacción con APIs, bases de datos o sistemas de archivos.  
* **Configuración:** core/config.py \- Gestión de persistencia siguiendo el estándar **XDG Base Directory** (ej. \~/.config/app\_name/).

### **Inyección de Dependencias**

Evitar instanciar servicios pesados dentro de otros. Pasa las dependencias (clientes API, conexiones DB) a través de los constructores (\_\_init\_\_) para facilitar el testing y la modularidad.

## **2\. Capa de Negocio y Modelo de Datos**

* **Validación de Esquemas:** En Python, usar Pydantic o dataclasses con Type Hints para validar datos externos antes de procesarlos.  
* **Estado Inmutable:** El estado de la aplicación debe ser predecible. No usar variables globales; preferir objetos de estado pasados entre servicios.  
* **POO y Herencia:** Utilizar clases para representar entidades. Implementar herencia en componentes con comportamientos compartidos (ej. una clase BaseMenu para todos los menús de la app).

## **3\. Interfaz Visual y UX (Diseño Humano)**

### **Filosofía de Entrada**

* **Cero Texto Libre:** El usuario nunca debe escribir rutas o nombres si pueden ser seleccionados. Usar Questionary o Inquirer para menús de flechas.  
* **Breadcrumbs:** Mostrar la ruta de navegación (ej. Ajustes \> Seguridad \> API Key) para orientar al usuario.

### **Consistencia Visual y Tematización**

* **Temas Centralizados:** Definir un objeto Theme con la paleta de colores:  
  * 🔵 **Cian/Azul:** Títulos, encabezados y prompts.  
  * 🟢 **Verde:** Éxito y confirmaciones.  
  * 🟡 **Amarillo:** Advertencias o estados de espera.  
  * 🔴 **Rojo:** Errores críticos.  
* **Componentes Rich:** Toda información estructurada debe mostrarse en Table, Panel o Tree. Usar Progress o Status (spinners) para procesos \>500ms.  
* **Feedback:** stdout para interfaz, stderr para logs de sistema y errores.

## **4\. Documentación Obligatoria e Interactiva**

**Regla de Oro:** La documentación no es opcional, es parte del código.

* **Archivos Base:** Generar siempre README.md (uso rápido) y docs/manual.md (detallado).  
* **Acceso Integrado:** El menú principal debe tener SIEMPRE una opción "Ayuda/Documentación" que abra un visor interno (usando el componente Markdown de Rich) para leer los archivos .md del proyecto sin salir de la app.

## **5\. Integraciones y Resiliencia**

* **Gestión de Secretos:** Prohibido el "hardcode". Usar .env o variables de entorno. Ofrecer un comando setup visual para configurar credenciales.  
* **Políticas de Red:** Implementar reintentos con *Exponential Backoff* para APIs externas.  
* **Abstracción:** Usar el patrón *Repository* para que la lógica de negocio no dependa del formato de almacenamiento (JSON, SQLite, etc.).

## **6\. Automatización y Modo "Headless" (Modo Máquina)**

Las apps deben detectar su entorno de ejecución (sys.stdin.isatty()):

* **Flag \--json:** Si se activa, la app omite la interfaz visual y devuelve solo JSON puro a stdout.  
* **Flag \--no-input / \-y:** Salta confirmaciones y usa valores por defecto para scripts de automatización.  
* **Exit Codes Semánticos:** 0 para éxito, 1 error general, 64 error de argumentos, 127 comando no encontrado.

## **7\. Gestión de Errores y Diagnóstico**

* **Graceful Shutdown:** Capturar SIGINT (Ctrl+C) para cerrar procesos limpiamente y mostrar un mensaje de despedida.  
* **Fail-Fast:** Validar pre-condiciones (red, permisos, archivos) al arrancar.  
* **Debug Mode:** Implementar flag \--debug que guarde logs detallados en un archivo en el directorio XDG, nunca en la pantalla principal.

## **8\. Reglas de Oro para la IA (Prompting)**

1. **Strict Typing:** Uso obligatorio de Type Hints en Python.  
2. **Documentación Inline:** Docstrings en cada clase y método principal.  
3. **Idempotencia:** Los comandos deben poder ejecutarse varias veces sin corromper el sistema.  
4. **No Sorpresas:** Pedir confirmación clara para acciones destructivas, a menos que se use \--force.
5. **Instalación de dependencias:** generar un fichero con las dependencias que necesita el proyecto, e incluir al arranque una comprobación previa. Si faltan dedendencias, preguntar al usuario si desea instlarlas (e intalarlas si el usuari acepta. Para entornos desatendidos, salir con un error a no ser que se le indique al programa que instale automaticamente las dependencias faltantes)

## **9\. Plantilla de Estructura de Proyecto**

proyecto\_cli/  
├── main.py                 \# Punto de entrada y CLI Parser  
├── README.md               \# Documentación rápida  
├── docs/  
│   └── manual.md           \# Manual de usuario detallado  
├── core/  
│   ├── config.py           \# Persistencia XDG y Secretos  
│   └── exceptions.py       \# Errores personalizados  
├── models/  
│   └── schemas.py          \# Modelos de datos (Pydantic/Dataclasses)  
├── services/  
│   └── business\_logic.py   \# Lógica central (POO)  
├── data/  
│   └── repository.py       \# Acceso a datos / APIs  
└── ui/  
    ├── theme.py            \# Paleta de colores y estilos Rich  
    ├── components.py       \# Elementos visuales reutilizables  
    └── doc\_viewer.py       \# Lógica para renderizar Markdown  

# **📦 Anexo 1: Gestión de Entornos y Dependencias (PEP 668\)**

## **1\. El Problema: "Externally Managed Environment"**

Los sistemas operativos modernos (basados en Debian/Ubuntu recientes, Alpine, etc.) bloquean la instalación global de paquetes de Python a través de pip para evitar corromper los paquetes gestionados por el gestor del sistema (como apt). Si intentas hacer un pip install global, recibirás el error *externally-managed-environment*.

**Regla Estricta:** Nunca uses sudo pip install ni modifiques las variables de entorno para saltarte esta protección. La única solución estándar y profesional para nuestras aplicaciones CLI es el uso de **Entornos Virtuales Locales (venv)**.

## **2\. Solución Estándar: Implementación del venv**

Toda aplicación CLI desarrollada bajo esta guía debe encapsular sus dependencias.

### **Paso 1: Preparar el sistema (Solo la primera vez)**

Asegúrate de que el sistema tiene soporte completo para entornos virtuales:

sudo apt update  
sudo apt install python3-venv python3-full

### **Paso 2: Crear el entorno virtual en el proyecto**

Dentro de la raíz del proyecto (ej. /opt/mi-cli/), crea un entorno oculto llamado .venv:

cd /opt/mi-cli  
python3 \-m venv .venv

### **Paso 3: Activar e instalar dependencias**

Siempre que necesites desarrollar o añadir nuevos paquetes, activa el entorno:

source .venv/bin/activate

*(Notarás que el prompt cambia a (.venv) usuario@host)*

## **3\. Mejores Prácticas: requirements.txt**

Está prohibido instalar paquetes sin documentarlos. El proyecto debe tener en su raíz un archivo requirements.txt.

**Ejemplo de requirements.txt:**

rich\>=13.0.0  
questionary\>=2.0.0  
typer\>=0.9.0

**Instalación automatizada:**

Con el entorno activado, instala todo el bloque mediante:

pip install \-r requirements.txt

## **4\. Ejecución Transparente (El "Shebang Trick")**

**El objetivo de una buena CLI es que el usuario final NO tenga que activar manualmente el entorno (source .venv/bin/activate) para usarla.**

Para lograr que el comando funcione directamente (ej. al hacer un enlace simbólico en /usr/local/bin), debes modificar la primera línea (Shebang) del archivo orquestador main.py para que apunte al intérprete Python *dentro* del entorno virtual.

**Sustituir:**

\#\!/usr/bin/env python3

**Por la ruta absoluta al venv (ejemplo si la app está en /opt/media-tools):**

\#\!/opt/media-tools/.venv/bin/python

De esta forma, al ejecutar ./main.py o llamar a la herramienta globalmente, Python utilizará automáticamente las librerías (rich, questionary, etc.) aisladas en ese directorio, manteniendo el sistema operativo limpio y seguro.


#!/usr/bin/env python3
"""
Esqueleto Base para Aplicaciones CLI Profesionales.
Sigue los estándares de la "Guía Maestra de Desarrollo CLI".
Incluye: Gestión de UI (Rich/Questionary), Configuración (XDG) y Visor de Documentación.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Callable

# Dependencias de terceros necesarias: pip install rich questionary
from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
import questionary


# ==========================================
# CAPA DE CONFIGURACIÓN Y PERSISTENCIA (CORE)
# ==========================================
class ConfigManager:
    """Gestiona la configuración local usando el estándar XDG Base Directory."""
    
    def __init__(self, app_name: str):
        self.app_name = app_name
        # Define ruta ~/.config/app_name/
        xdg_config = os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")
        self.config_dir = Path(xdg_config) / app_name
        self.config_file = self.config_dir / "config.json"
        self.data: Dict[str, Any] = {}
        
        self._init_config()

    def _init_config(self) -> None:
        """Asegura que el directorio y el archivo de configuración existan."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if not self.config_file.exists():
            self.save({"first_run": True, "theme": "default"})
        self.load()

    def load(self) -> None:
        """Carga los datos del archivo JSON en memoria."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            self.data = {}

    def save(self, new_data: Dict[str, Any] = None) -> None:
        """Guarda la configuración actual en el disco."""
        if new_data:
            self.data.update(new_data)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4)


# ==========================================
# CAPA DE PRESENTACIÓN E INTERFAZ (UI)
# ==========================================
class UIManager:
    """Centraliza todo el renderizado visual y la interacción con el usuario."""
    
    def __init__(self):
        # Paleta de colores semántica según la Guía Maestra
        self.theme = Theme({
            "info": "cyan",
            "warning": "yellow",
            "error": "bold red",
            "success": "bold green",
            "header": "bold magenta",
            "breadcrumb": "dim white"
        })
        self.console = Console(theme=self.theme)

    def clear(self) -> None:
        """Limpia la pantalla de la terminal."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def show_header(self, title: str, breadcrumb: str = "") -> None:
        """Muestra el título principal y la ruta de navegación actual."""
        self.clear()
        if breadcrumb:
            self.console.print(f"[{self.theme.styles['breadcrumb']}]{breadcrumb}[/]")
        self.console.print(Panel(f"[bold cyan]{title.upper()}[/]", border_style="blue", expand=False))
        self.console.print() # Línea en blanco

    def show_message(self, text: str, msg_type: str = "info") -> None:
        """Muestra un mensaje con el icono y color adecuado."""
        icons = {"success": "✅", "error": "❌", "warning": "⚠️", "info": "ℹ️"}
        icon = icons.get(msg_type, "•")
        self.console.print(f"{icon} [{msg_type}]{text}[/{msg_type}]")

    def ask_menu(self, message: str, choices: List[str]) -> str:
        """Renderiza un menú interactivo navegable con flechas."""
        return questionary.select(
            message,
            choices=choices,
            style=questionary.Style([
                ('pointer', 'fg:cyan bold'),
                ('highlighted', 'fg:cyan'),
                ('selected', 'fg:green'),
            ])
        ).ask()

    def with_spinner(self, message: str, func: Callable, *args, **kwargs) -> Any:
        """Ejecuta una función mientras muestra un spinner de carga."""
        with self.console.status(f"[cyan]{message}...[/]", spinner="dots"):
            return func(*args, **kwargs)

    def show_documentation(self) -> None:
        """Busca y renderiza archivos Markdown del proyecto."""
        # Generar un README.md dummy si no existe para la demostración
        if not Path("README.md").exists():
            with open("README.md", "w", encoding="utf-8") as f:
                f.write("# Documentación de Prueba\n\nEsta es una app generada desde el **Esqueleto Base**.\n\n- Soporta Markdown.\n- Usa POO.")

        md_files = list(Path(".").glob("*.md")) + list(Path("docs").glob("*.md"))
        
        if not md_files:
            self.show_message("No se encontraron archivos de documentación (.md).", "warning")
            time.sleep(2)
            return

        choices = [f.name for f in md_files] + ["Volver al Menú Principal"]
        self.show_header("Visor de Documentación", "Inicio > Documentación")
        
        choice = self.ask_menu("Selecciona el documento a leer:", choices)
        if choice == "Volver al Menú Principal" or choice is None:
            return

        selected_file = next(f for f in md_files if f.name == choice)
        
        with open(selected_file, 'r', encoding='utf-8') as f:
            md_content = Markdown(f.read())
            
        self.clear()
        self.console.print(Panel(md_content, title=f" 📖 {choice} ", border_style="cyan"))
        self.console.print()
        questionary.press_any_key_to_stop("Presiona cualquier tecla para volver...").ask()


# ==========================================
# CAPA DE ORQUESTACIÓN (MAIN)
# ==========================================
class AppLogic:
    """Clase principal que orquesta la lógica de negocio y une Config con UI."""
    
    def __init__(self, app_name: str):
        self.config = ConfigManager(app_name)
        self.ui = UIManager()
        self.app_name = app_name

    def run_dummy_task(self) -> None:
        """Ejemplo de una tarea de negocio."""
        self.ui.show_header("Ejecutando Tarea", "Inicio > Tarea")
        
        # Simulamos un proceso de red o cálculo complejo
        def mock_process():
            time.sleep(2)
            return True
            
        success = self.ui.with_spinner("Procesando datos en la nube", mock_process)
        
        if success:
            self.ui.show_message("Tarea completada con éxito.", "success")
        
        time.sleep(1.5)

    def main_loop(self) -> None:
        """Bucle principal de la aplicación."""
        while True:
            self.ui.show_header(f"Bienvenido a {self.app_name}", "Inicio")
            
            opciones = [
                "1. Ejecutar Tarea de Prueba",
                "2. Ver Configuración",
                "3. Ayuda y Documentación",
                "4. Salir"
            ]
            
            seleccion = self.ui.ask_menu("¿Qué deseas hacer?", opciones)

            if seleccion is None or "Salir" in seleccion:
                self.ui.show_message("Saliendo de la aplicación... ¡Hasta pronto!", "info")
                break
            elif "Ejecutar" in seleccion:
                self.run_dummy_task()
            elif "Configuración" in seleccion:
                self.ui.show_header("Configuración Actual", "Inicio > Configuración")
                self.ui.console.print(self.config.data)
                questionary.press_any_key_to_stop("\nPresiona para volver...").ask()
            elif "Ayuda" in seleccion:
                self.ui.show_documentation()


def main():
    """Punto de entrada estandarizado."""
    app = AppLogic(app_name="mi_app_maestra")
    try:
        app.main_loop()
    except KeyboardInterrupt:
        # Graceful Shutdown
        app.ui.console.print("\n[warning]Operación cancelada por el usuario (Ctrl+C). Saliendo limpiamente...[/]")
        sys.exit(0)
    except Exception as e:
        # Captura global de errores visual
        app.ui.console.print(Panel(f"[bold red]Error Inesperado:[/]\n{str(e)}", border_style="red"))
        sys.exit(1)

if __name__ == "__main__":
    main()