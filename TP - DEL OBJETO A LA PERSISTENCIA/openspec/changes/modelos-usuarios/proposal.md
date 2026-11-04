# Proposal

## Why

El Ejercicio 2 del parcial (14 %) y las páginas 4 a 6 de la consigna introducen el modelo de dominio para autenticación, autorización y auditoría de seguridad. Actualmente, la aplicación carece del módulo `usuarios` y de las entidades `usuario`, `asignacion_rol`, `intento_acceso` y `evento_seguridad`.

CHG-06 (`modelos-usuarios`) es un cambio prioritario (P1) asignado a Lauti en `PLAN_PARCIAL.md`. Junto con CHG-07 (`modelos-libro-cliente-stock`), provee las entidades necesarias para que Nico pueda generar la migración 0003 en CHG-08, la cual destraba la autenticación (CHG-11), los repositorios de catálogo y clientes (CHG-13, 15) y la carga inicial (CHG-17).

## What Changes

- Crear `app/modules/usuarios/__init__.py`.
- Crear `app/modules/usuarios/models.py` con las siguientes entidades basadas en SQLModel:
  - `Usuario`:
    - Tabla: `usuario`.
    - Columnas: `id` (PK), `email` (único, `Field(unique=True)` sin `index=True` -> `uq_usuario_email`), `nombre`, `password_hash`, `activo` (default True), `debe_cambiar_password` (default False).
    - Sin columna `rol` (los roles viven en `asignacion_rol`).
    - Relación bidireccional con `AsignacionRol` (`Usuario.asignaciones` <-> `AsignacionRol.usuario`).
  - `AsignacionRol`:
    - Tabla: `asignacion_rol`.
    - Columnas: `id` (PK), `usuario_id` (FK a `usuario.id`, index=True), `rol` (str), `desde` (`timestamptz`), `vence_en` (`timestamptz`, nullable), `revocada_en` (`timestamptz`, nullable), `otorgada_por` (FK a `usuario.id`, index=True, nullable).
    - `CheckConstraint("rol IN ('ADMIN', 'VENDEDOR', 'CLIENTE')", name="rol_valido")` -> constraint nombrada `ck_asignacion_rol_rol_valido`.
    - Índice único parcial: `Index("uq_asignacion_rol_usuario_rol_vigente", "usuario_id", "rol", unique=True, postgresql_where=text("revocada_en IS NULL"))`.
    - Relaciones explícitas hacia `Usuario` (`usuario` y `otorgada_por_usuario`) con `sa_relationship_kwargs={"foreign_keys": ...}` para evitar ambigüedades.
  - `IntentoAcceso`:
    - Tabla: `intento_acceso`.
    - Columnas: `id` (PK), `cuando` (`timestamptz`), `email` (str), `ip` (str), `exito` (bool).
    - Índice compuesto: `Index("ix_intento_acceso_email_ip_cuando", "email", "ip", "cuando")`.
  - `EventoSeguridad`:
    - Tabla: `evento_seguridad`.
    - Columnas: `id` (PK), `cuando` (`timestamptz`), `actor` (texto), `accion` (texto).
  - Reglas de convención:
    - Primer import en `models.py`: `import app.core.base  # noqa: F401`.
    - Todas las columnas de fecha son con zona horaria (`DateTime(timezone=True)`).
- Registrar los 4 modelos en `app/models.py`.
- **Acuerdo de interfaz con Nicolás (CHG-07)**:
  - CHG-06 no declara `Usuario.cliente` ni `Cliente.usuario`. CHG-07 incorpora juntos ambos extremos de la relación Cliente–Usuario: `Cliente.usuario` y `Usuario.cliente`; este último es escalar mediante `sa_relationship_kwargs={"uselist": False}`.
  - La relación de movimientos también se completa en CHG-07 con ambos extremos: `MovimientoStock.usuario` y `Usuario.movimientos`.
  - El índice único parcial de roles vigentes adopta el nombre simétrico pactado: `uq_asignacion_rol_usuario_rol_vigente`.

**Fuera de alcance**:
- Esquemas Pydantic y DTOs de autenticación y usuarios (CHG-09a).
- Endpoints de autenticación (`/auth/*`, CHG-11) y administración de usuarios (CHG-14).
- Migración 0003 de Alembic (CHG-08).
- Relaciones Cliente–Usuario (`Cliente.usuario` y `Usuario.cliente`) y MovimientoStock–Usuario (`MovimientoStock.usuario` y `Usuario.movimientos`), cuyos dos extremos se incorporan en CHG-07.

## Capabilities

### New Capabilities
- `modelos-usuarios`: Definición y restricciones de base de datos para la gestión de usuarios, asignación histórica de roles y auditoría de eventos de acceso y seguridad.

### Modified Capabilities
Ninguna.

## Impact

- **Código**:
  - `app/modules/usuarios/__init__.py` (nuevo)
  - `app/modules/usuarios/models.py` (nuevo)
  - `app/models.py` (registro de los 4 modelos)
- **Tests**:
  - `tests/test_usuarios_models.py` (nuevo)
  - `tests/test_naming_convention.py` (ampliado con modelos de `usuarios`)
- **Desbloquea**: CHG-08 (migración 0003 junto con CHG-07) y CHG-09a (schemas de usuarios).
