# Reglas de Desarrollo

Normas obligatorias para trabajar en `media-tools` con un criterio técnico uniforme.

## 1. Arquitectura

- `ui/` solo interactúa y renderiza.
- `services/` contiene lógica de negocio reutilizable.
- `data/` encapsula herramientas externas y acceso a filesystem.
- `models/` contiene estructuras tipadas simples.
- `main.py` solo hace wiring y callbacks.

## 2. Configuración

- reutilizar siempre `self.config` de `CLIBaseApp`,
- no crear un segundo `ConfigManager`,
- evitar rutas hardcodeadas.

## 3. Calidad de código

- type hints en firmas públicas,
- docstrings en clases y funciones relevantes,
- funciones pequeñas y con una sola responsabilidad,
- nombres explícitos.

## 4. Seguridad operativa

- no modificar archivos sin confirmación,
- validar binarios y permisos antes de operar,
- fallar pronto ante rutas inválidas o herramientas ausentes.

## 5. Testing

Todo cambio relevante debe acompañarse de:

- tests del servicio afectado,
- tests del repositorio o adaptador externo,
- tests de UI o de flujo interactivo cuando haya interacción nueva,
- actualización de docs si cambia el comportamiento visible.

## 6. Ejemplo de decisión correcta

Correcto:

```python
summary = service.audit(selection)
render_audit_summary(summary)
```

Incorrecto:

```python
service.audit_and_print(selection)
```

## 7. Checklist rápido

1. la capa correcta implementa el cambio,
2. no se rompe el flujo de dependencias,
3. los tests pasan,
4. la documentación quedó alineada.
