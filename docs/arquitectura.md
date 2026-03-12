# Arquitectura del Proyecto

Este proyecto sigue la **Guía Maestra de Desarrollo CLI**.

## Arquitectura N-Tier

media-tools
├── main.py                 # Entrypoint CLI
├── core/                   # Configuración y errores
├── models/                 # Modelos de datos
├── services/               # Lógica de negocio
├── data/                   # Acceso a datos
├── ui/                     # Interfaz CLI
├── docs/                   # Documentación
└── scripts/                # Scripts auxiliares

## Capas

### Entrypoint

main.py  
Gestiona comandos CLI mediante Typer.

### UI

Renderizado visual usando Rich y Questionary.

### Services

Lógica de negocio desacoplada de la interfaz.

### Repository

Acceso al filesystem y análisis multimedia.

### Models

Estructuras de datos tipadas.

### Core

Configuración del sistema y utilidades base.
