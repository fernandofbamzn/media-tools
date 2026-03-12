#!/usr/bin/env bash

set -e

DOCS_DIR="docs"
PROJECT_NAME="media-tools"

mkdir -p "$DOCS_DIR"

echo "Generando documentación del proyecto..."

cat > "$DOCS_DIR/arquitectura.md" << 'EOF'
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
EOF


cat > "$DOCS_DIR/requisitos.md" << 'EOF'
# Requisitos del Proyecto

## Sistema

- Linux (preferiblemente Debian/Ubuntu)
- Python >= 3.10
- mkvtoolnix
- ffmpeg
- mediainfo

## Python

Dependencias principales:

- rich
- questionary
- typer
- pydantic

Instalación:

pip install -r requirements.txt

## Entorno recomendado

Virtualenv local:

python3 -m venv .venv
source .venv/bin/activate
EOF


cat > "$DOCS_DIR/fases_desarrollo.md" << 'EOF'
# Fases de Desarrollo

## Fase 1 — Base del proyecto

Objetivo: infraestructura CLI profesional

Incluye:

- arquitectura N-tier
- separación de capas
- verificación de dependencias
- visor de documentación
- entorno virtual

Estado: COMPLETADO

---

## Fase 2 — Navegación y auditoría

Objetivo: análisis de biblioteca multimedia

Incluye:

- navegador interactivo
- auditoría de idiomas
- análisis de códecs
- detección preliminar de duplicados

Estado: EN PROGRESO

---

## Fase 3 — Planificador de cambios

Objetivo: modificar archivos de forma segura

Incluye:

- eliminar pistas duplicadas
- seleccionar idiomas
- eliminar subtítulos innecesarios
- informe previo de cambios

Estado: PENDIENTE

---

## Fase 4 — Optimización de vídeo

Objetivo: reducir tamaño de archivos

Incluye:

- transcodificación opcional
- perfiles de calidad
- estimación de ahorro

Estado: FUTURO

---

## Fase 5 — Automatización

Objetivo: modo headless para pipelines

Incluye:

- salida JSON
- ejecución sin interacción
- integración con scripts
EOF


echo "Documentación generada en /docs"
