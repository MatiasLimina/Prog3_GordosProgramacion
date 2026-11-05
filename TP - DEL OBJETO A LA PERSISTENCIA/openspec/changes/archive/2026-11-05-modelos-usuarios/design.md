# Design

## Context

El proyecto incorpora el módulo de usuarios, roles y seguridad según la Figura 1 (pág. 5 de la consigna) y las reglas de negocio RN-01, RN-03, RN-04, RN-07 y RN-16.
Para mantener el flujo de trabajo desacoplado y sin cuellos de botella entre integrantes (Lauti en CHG-06 y Nico en CHG-07), este change se enfoca exclusivamente en la persistencia de las entidades de acceso y seguridad.

## Goals / Non-Goals

**Goals:**
- Implementar los modelos `Usuario`, `AsignacionRol`, `IntentoAcceso` y `EventoSeguridad` con SQLModel y SQLAlchemy.
- Asegurar que las constraints sigan la convención unificada (`uq_`, `ck_`, `ix_`).
- Implementar el índice único parcial `uq_asignacion_rol_usuario_rol_vigente` sobre `(usuario_id, rol) WHERE revocada_en IS NULL`.
- Implementar el índice compuesto `ix_intento_acceso_email_ip_cuando`.
- Registrar los modelos en `app/models.py`.
- Suite de tests unitarios que verifique tablas, columnas, constraints, índices y configuración de mappers sin requerir PostgreSQL levantado.

**Non-Goals:**
- Contratos y schemas Pydantic de entrada/salida (CHG-09a).
- Declaración de las relaciones bidireccionales con `Cliente` y `MovimientoStock` (ambos extremos de cada relación se incorporan en CHG-07).
- Generación de la migración 0003 en Alembic (CHG-08).

## Decisions

### D1 · Desacoplamiento temporal de relaciones cruzadas en `Usuario` (Acuerdo con Nico)
SQLAlchemy valida la consistencia de las relaciones (`back_populates`) al ejecutar `configure_mappers()`. Por eso CHG-06 no declara ninguno de los extremos de las relaciones Cliente–Usuario ni MovimientoStock–Usuario.
- **Decisión**: `Usuario` solo declara en CHG-06 la relación con `AsignacionRol` (`asignaciones`). CHG-07 incorpora juntos `Cliente.usuario` y `Usuario.cliente`, además de `MovimientoStock.usuario` y `Usuario.movimientos`. El extremo `Usuario.cliente` es escalar y usa `sa_relationship_kwargs={"uselist": False}`; los tipos cruzados se mantienen como referencias string bajo `TYPE_CHECKING`.

### D2 · Nombres canónicos de constraints e índices parciales
Para garantizar que la traducción de `IntegrityError` (en `app/core/errors.py`) asigne mensajes específicos sin caer en genéricos:
- `uq_usuario_email`: Generado automáticamente mediante `Field(unique=True)` sin `index=True` gracias a la convención de `app.core.base`.
- `ck_asignacion_rol_rol_valido`: Mediante `CheckConstraint("rol IN ('ADMIN', 'VENDEDOR', 'CLIENTE')", name="rol_valido")`.
- `uq_asignacion_rol_usuario_rol_vigente`: Índice único parcial definido en `__table_args__` con `postgresql_where=text("revocada_en IS NULL")`. Se adopta el sufijo `_vigente` acordado con Nico (en paralelo a `uq_libro_isbn_vigente`).
- `ix_intento_acceso_email_ip_cuando`: Índice multi-columna en `__table_args__`.

### D3 · Desambiguación de claves foráneas múltiples en `AsignacionRol`
Dado que `asignacion_rol` referencia a `usuario.id` a través de dos claves foráneas (`usuario_id` como titular y `otorgada_por` como emisor opcional), SQLAlchemy exige desambiguar la clave foránea a usar en las relaciones:
```python
usuario: Optional["Usuario"] = Relationship(
    back_populates="asignaciones",
    sa_relationship_kwargs={"foreign_keys": "[AsignacionRol.usuario_id]"},
)
otorgada_por_usuario: Optional["Usuario"] = Relationship(
    sa_relationship_kwargs={"foreign_keys": "[AsignacionRol.otorgada_por]"},
)
```
Y en `Usuario`:
```python
asignaciones: list["AsignacionRol"] = Relationship(
    back_populates="usuario",
    sa_relationship_kwargs={"foreign_keys": "[AsignacionRol.usuario_id]"},
)
```

### D4 · Fechas con zona horaria obligatoria (`timestamptz`)
En cumplimiento de la consigna (pág. 6: «Todas las fechas nuevas son timestamptz»), todas las columnas temporales (`desde`, `vence_en`, `revocada_en`, `cuando`) se configuran con `sa_type=DateTime(timezone=True)`.
