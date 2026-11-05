# Spec Delta

## Purpose

Define las entidades de persistencia para usuarios, asignación histórica de roles y auditoría de eventos de acceso y seguridad (CHG-06).

## ADDED Requirements

### Requirement: Definición del modelo Usuario
El sistema SHALL definir el modelo de tabla `Usuario` mapeado a `usuario` con clave primaria `id`, `email` único sin índice redundante, `nombre`, `password_hash`, `activo`, `debe_cambiar_password` y relación `asignaciones`. El modelo SHALL NOT tener columna `rol`.

#### Scenario: Atributos y restricciones de Usuario
- **WHEN** se inspecciona la tabla `usuario` en el metadata
- **THEN** posee las columnas `id`, `email`, `nombre`, `password_hash`, `activo`, `debe_cambiar_password`, la constraint `uq_usuario_email`, sin columna `rol` ni índice `ix_usuario_email`

#### Scenario: Relación de usuario con asignaciones de rol
- **WHEN** se inspecciona la relación `asignaciones` en `Usuario`
- **THEN** referencia a `AsignacionRol.usuario` como colección

### Requirement: Integración de la relación Cliente–Usuario en CHG-07
CHG-06 SHALL NOT declarar ninguno de los extremos de la relación Cliente–Usuario (`Cliente.usuario` ni `Usuario.cliente`). CHG-07 SHALL incorporar ambos extremos juntos: `Cliente.usuario` y `Usuario.cliente`, siendo este último escalar mediante `sa_relationship_kwargs={"uselist": False}`.

#### Scenario: Extremos de Cliente–Usuario incorporados juntos
- **WHEN** se implementa la relación Cliente–Usuario en CHG-07
- **THEN** `Cliente.usuario` y `Usuario.cliente` se declaran en ese mismo change, y `Usuario.cliente` es escalar con `uselist=False`

### Requirement: Definición del modelo AsignacionRol
El sistema SHALL definir el modelo `AsignacionRol` sobre `asignacion_rol` con FKs indexadas a `usuario`, CHECK de roles permitidos e índice único parcial para roles vigentes.

#### Scenario: Restricción de roles válidos
- **WHEN** se define la tabla `asignacion_rol`
- **THEN** incluye la constraint `ck_asignacion_rol_rol_valido` exigiendo `ADMIN`, `VENDEDOR` o `CLIENTE`

#### Scenario: Índice único parcial de rol vigente
- **WHEN** se inspeccionan los índices de `asignacion_rol`
- **THEN** existe el índice único parcial `uq_asignacion_rol_usuario_rol_vigente` sobre `(usuario_id, rol)` con filtro `revocada_en IS NULL`

#### Scenario: Fechas con zona horaria
- **WHEN** se examinan las columnas `desde`, `vence_en` y `revocada_en`
- **THEN** son de tipo `DateTime` con `timezone=True`

### Requirement: Definición del modelo IntentoAcceso
El sistema SHALL definir el modelo `IntentoAcceso` sobre `intento_acceso` con marca temporal con zona, datos del intento e índice compuesto de búsqueda.

#### Scenario: Índice compuesto de auditoría de intentos
- **WHEN** se inspeccionan los índices de `intento_acceso`
- **THEN** existe el índice `ix_intento_acceso_email_ip_cuando` sobre `(email, ip, cuando)`

### Requirement: Definición del modelo EventoSeguridad
El sistema SHALL definir el modelo `EventoSeguridad` sobre `evento_seguridad` con marca temporal con zona, actor y acción.

#### Scenario: Estructura de auditoría de eventos
- **WHEN** se inspecciona la tabla `evento_seguridad`
- **THEN** contiene las columnas `id`, `cuando` (timestamptz), `actor` y `accion` sin FKs hacia otras tablas

### Requirement: Convenciones y Registro de Modelos
El módulo `app/modules/usuarios/models.py` SHALL aplicar la convención de constraints antes de definir tablas y registrar los modelos en `app/models.py`.

#### Scenario: Naming convention al importar
- **WHEN** se importa `app.modules.usuarios.models` de forma aislada
- **THEN** sus constraints adoptan los prefijos `uq_`, `ck_`, `fk_` y `ix_`

#### Scenario: Registro central en app/models.py
- **WHEN** se importa `app.models`
- **THEN** `SQLModel.metadata.tables` contiene las 4 tablas del módulo `usuarios`
