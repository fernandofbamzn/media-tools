# Reglas de Desarrollo del Proyecto

Estas reglas definen los principios obligatorios para modificar o extender el proyecto **media-tools**.

Están diseñadas para que **desarrolladores humanos y agentes IA** puedan trabajar en el proyecto sin romper su arquitectura.

---

# 1. Arquitectura del Proyecto

El proyecto sigue una arquitectura CLI modular de capas (N-Tier).

Estructura obligatoria:

media-tools
├── main.py
├── core/
├── models/
├── services/
├── data/
├── ui/
├── docs/
└── scripts/

## Responsabilidad de cada capa

### main.py

Entrypoint de la aplicación.

Responsabilidades:

- registrar comandos CLI
- inicializar servicios
- manejo global de errores
- verificación de dependencias

No debe contener lógica de negocio.

---

### core/

Infraestructura base del proyecto.

Contiene:

- gestión de configuración
- errores personalizados
- utilidades internas

No debe contener lógica específica de la aplicación.

---

### models/

Modelos de datos.

Reglas:

- usar dataclasses o pydantic
- incluir type hints
- los modelos deben ser simples y predecibles

Ejemplos:

MediaFile  
Track  
AuditReport

---

### services/

Contiene toda la lógica de negocio.

Ejemplos:

BrowseService  
AuditService  
MediaToolsService

Reglas:

- no depender de la UI
- no imprimir en consola
- no pedir input al usuario

Los servicios deben ser testables.

---

### data/

Acceso a datos externos.

Ejemplos:

- filesystem
- mkvmerge
- APIs futuras

Patrón obligatorio:

Repository Pattern

Ejemplo:

MediaRepository

---

### ui/

Renderizado visual.

Tecnologías:

- rich
- questionary

Reglas:

- solo lógica de interfaz
- nunca lógica de negocio

Ejemplos:

theme.py  
components.py  
menus.py

---

# 2. Principios de Diseño

## Separación estricta de capas

UI → Services → Repository → Models

Nunca al revés.

Incorrecto:

UI llamando mkvmerge directamente

Correcto:

UI → Service → Repository → mkvmerge

---

## No Hardcoding

Evitar rutas fijas.

Incorrecto:

/mnt/Filmoteca

Correcto:

configurable vía core/config.py

---

## Idempotencia

Las operaciones deben poder ejecutarse varias veces sin romper el sistema.

Ejemplos:

- no sobrescribir archivos sin confirmación
- evitar cambios irreversibles

---

## Fail Fast

Validar condiciones antes de ejecutar acciones críticas.

Ejemplos:

- comprobar binarios (mkvmerge)
- comprobar permisos
- comprobar rutas

---

# 3. Reglas de Código

## Type Hints obligatorios

Todas las funciones públicas deben tener type hints.

Ejemplo:

def scan(self, root: Path) -> List[Path]:

---

## Docstrings obligatorios

Toda clase y método público debe tener docstring.

Ejemplo:

"""Analiza un archivo multimedia y devuelve sus pistas."""

---

## Funciones pequeñas

Preferir funciones cortas y claras.

Evitar funciones de más de 80-100 líneas.

---

# 4. Interfaz CLI

La CLI se implementa con Typer.

Reglas:

- cada comando debe tener docstring
- los comandos deben ser simples
- no duplicar lógica entre comandos

Ejemplo:

media-tools doctor  
media-tools browse  
media-tools audit

---

# 5. Seguridad

El proyecto no debe modificar archivos sin confirmación del usuario.

Las acciones destructivas deben requerir confirmación explícita.

Ejemplo:

¿Eliminar pistas duplicadas?

---

# 6. Flujo de Desarrollo

Antes de añadir funcionalidades:

1. Revisar docs/fases_desarrollo.md
2. Identificar la fase actual
3. Implementar cambios solo en la fase correspondiente

---

# 7. Uso por Agentes IA

Los agentes IA deben seguir este proceso:

1. Leer:

docs/arquitectura.md  
docs/dev_rules.md  
docs/fases_desarrollo.md

2. Entender la arquitectura.

3. Implementar cambios respetando:

- capas
- responsabilidades
- reglas de código

4. Nunca modificar múltiples capas sin justificación.

---

# 8. Regla Principal

Si un cambio rompe la arquitectura, el cambio es incorrecto.

La arquitectura del proyecto tiene prioridad sobre cualquier funcionalidad nueva.
