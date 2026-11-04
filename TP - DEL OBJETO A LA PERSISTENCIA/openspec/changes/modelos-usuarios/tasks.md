# Tasks

Strict TDD: Cada paso de verificación comienza con tests que fallan (RED) antes de escribir el código correspondiente (GREEN). Todos los tests de modelos se ejecutan en memoria analizando el metadata y los mappers sin requerir conexión a la base de datos de pruebas.

## 1. Definición y Precondiciones (Hito 1)

- [x] 1.1 Crear rama `feat/modelos-usuarios` desde `main`.
- [x] 1.2 Redactar artefactos OpenSpec (`proposal.md`, `specs/modelos-usuarios/spec.md`, `design.md`, `tasks.md`).
- [x] 1.3 Validar coherencia del change con `openspec.cmd validate modelos-usuarios --strict`.

## 2. Tests Unitarios y Verificación en Rojo (Hito 2 - TDD Red)

- [ ] 2.1 Crear `tests/test_usuarios_models.py` validando:
  - Registro de las tablas `usuario`, `asignacion_rol`, `intento_acceso` y `evento_seguridad` en `SQLModel.metadata.tables`.
  - Columnas esperadas, claves primarias y tipos (incluyendo `DateTime(timezone=True)`).
  - Constraints con convención de nombres: `uq_usuario_email`, `ck_asignacion_rol_rol_valido`.
  - Índices esperados: `ix_asignacion_rol_usuario_id`, `ix_asignacion_rol_otorgada_por`, `ix_intento_acceso_email_ip_cuando`.
  - Índice parcial único: `uq_asignacion_rol_usuario_rol_vigente` con filtro `WHERE revocada_en IS NULL`.
  - Ausencia de índice redundante `ix_usuario_email` (garantizando `unique=True` sin `index=True`).
  - Navegación bidireccional limpia entre `Usuario` y `AsignacionRol`, y configuración de mappers (`configure_mappers()`).
- [ ] 2.2 Extender `tests/test_naming_convention.py` incluyendo los modelos del módulo `usuarios`.
- [ ] 2.3 Ejecutar `pytest tests/test_usuarios_models.py tests/test_naming_convention.py` y verificar que fallen por `ModuleNotFoundError` (RED).

## 3. Implementación y Registro de Modelos (Hito 3 - TDD Green)

- [ ] 3.1 Crear `app/modules/usuarios/__init__.py`.
- [ ] 3.2 Crear `app/modules/usuarios/models.py` con:
  - `import app.core.base  # noqa: F401` al inicio.
  - Modelo `Usuario`.
  - Modelo `AsignacionRol`.
  - Modelo `IntentoAcceso`.
  - Modelo `EventoSeguridad`.
- [ ] 3.3 Registrar los 4 modelos en `app/models.py`.
- [ ] 3.4 Ejecutar `pytest tests/test_usuarios_models.py tests/test_naming_convention.py` y constatar que pasen al 100% (GREEN).
- [ ] 3.5 Ejecutar la suite completa de tests (`pytest -k "not test_db"`) y `ruff check app tests`.

## 4. Actualización y Cierre (Hito 4)

- [ ] 4.1 Actualizar `PLAN_PARCIAL.md` indicando el avance de CHG-06.
- [ ] 4.2 Validación final de OpenSpec (`openspec.cmd validate modelos-usuarios --strict`).
