# AGENTS.md

Guía para agentes IA que trabajen en el repositorio **media-tools**.

Este archivo define cómo entender el proyecto y cómo realizar cambios sin romper su arquitectura.

---

# 1. Objetivo del Proyecto

media-tools es una herramienta CLI para gestionar bibliotecas multimedia.

Funciones principales:

- analizar archivos MKV/MP4
- detectar pistas de audio y subtítulos
- eliminar pistas duplicadas
- seleccionar idiomas
- optimizar archivos multimedia
- generar auditorías de bibliotecas

El proyecto está diseñado para funcionar en **Linux**, normalmente dentro de contenedores **LXC/Proxmox**.

---

# 2. Tecnologías

Lenguaje principal:

Python 3

CLI:

Typer

Interfaz:

Rich  
Questionary

Herramientas externas:

mkvmerge  
ffmpeg  
mediainfo

---

# 3. Arquitectura del Proyecto

El proyecto sigue una arquitectura **N-Tier CLI**.

Estructura:

media-tools
├── main.py
├── core/
├── models/
├── services/
├── data/
├── ui/
├── docs/
└── scripts/

---

# 4. Responsabilidad de Cada Carpeta

## main.py

Entrypoint CLI.

Responsabilidades:

- registrar comandos Typer
- inicializar servicios
- verificación de dependencias
- manejo global de errores

Nunca colocar lógica de negocio aquí.

---

## core/

Infraestructura base.

Contiene:

- configuración
- verificación de dependencias
- excepciones personalizadas

---

## models/

Modelos de datos.

Reglas:

- usar dataclasses o pydantic
- usar type hints
- evitar lógica compleja

Ejemplos:

MediaFile  
Track  
AuditReport

---

## services/

Contiene la lógica de negocio.

Ejemplos:

BrowseService  
AuditService  
MediaToolsService

Reglas:

- no depender de la UI
- no pedir input al usuario
- no imprimir directamente en consola

Los servicios deben ser reutilizables.

---

## data/

Acceso a sistemas externos.

Ejemplos:

filesystem  
mkvmerge  
APIs futuras

Patrón utilizado:

Repository Pattern

Ejemplo:

MediaRepository

---

## ui/

Interfaz CLI.

Tecnologías:

Rich  
Questionary

Responsabilidades:

- renderizado visual
- menús interactivos
- mensajes al usuario

Nunca incluir lógica de negocio.

---

# 5. Flujo de Desarrollo

Antes de implementar cambios:

1. Leer:

docs/arquitectura.md  
docs/dev_rules.md  
docs/fases_desarrollo.md  

2. Identificar la fase actual.

3. Implementar cambios en la capa correcta.

---

# 6. Principios Importantes

## Separación de capas

UI → Services → Repository → Models

Nunca romper este flujo.

---

## No Hardcoding

Evitar rutas como:

/srv/media

Las rutas deben venir de configuración.

---

## Idempotencia

Las operaciones deben poder ejecutarse varias veces sin romper datos.

---

## Fail Fast

Validar condiciones antes de ejecutar acciones.

Ejemplos:

- comprobar mkvmerge
- comprobar permisos
- comprobar rutas

---

# 7. Convenciones de Código

Reglas obligatorias:

- usar type hints
- incluir docstrings
- funciones pequeñas y claras
- evitar funciones >100 líneas

---

# 8. Seguridad

El programa no debe modificar archivos sin confirmación del usuario.

Las acciones destructivas deben requerir confirmación explícita.

---

# 9. Estrategia de Cambios

Cambios grandes deben dividirse en pasos pequeños:

1. modificar modelos
2. modificar repositorio
3. modificar servicios
4. actualizar UI
5. actualizar CLI

Nunca modificar todas las capas a la vez sin motivo.

---

# 10. Regla Fundamental

Si una modificación rompe la arquitectura, la modificación es incorrecta.

La arquitectura del proyecto tiene prioridad sobre cualquier funcionalidad nueva.
