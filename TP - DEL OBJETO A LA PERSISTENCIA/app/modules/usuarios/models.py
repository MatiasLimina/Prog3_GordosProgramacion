# Antes que SQLModel defina la tabla: fija la naming convention de constraints.
import app.core.base  # noqa: F401

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, DateTime, Index, text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.clientes.models import Cliente
    from app.modules.libros.models import MovimientoStock


class Usuario(SQLModel, table=True):
    __tablename__ = "usuario"

    id: int | None = Field(default=None, primary_key=True)
    # unique SIN index: así se crea la constraint uq_usuario_email (clave del 409).
    email: str = Field(max_length=255, unique=True)
    nombre: str = Field(max_length=150)
    password_hash: str = Field(max_length=255)
    activo: bool = Field(default=True)
    debe_cambiar_password: bool = Field(default=False)

    # Declaradas en CHG-07 (acuerdo con Nico), junto con Cliente.usuario y MovimientoStock.usuario.
    # cliente: a uno (escalar); la FK vive en cliente.usuario_id (UNIQUE, nullable).
    cliente: Optional["Cliente"] = Relationship(
        back_populates="usuario", sa_relationship_kwargs={"uselist": False}
    )
    # movimientos: passive_deletes="all" y sin cascade de borrado: los usuarios no se borran
    # y movimiento_stock es de sólo agregado; el ORM nunca debe tocar esas filas.
    movimientos: list["MovimientoStock"] = Relationship(
        back_populates="usuario", sa_relationship_kwargs={"passive_deletes": "all"}
    )
    asignaciones: list["AsignacionRol"] = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs={"foreign_keys": "[AsignacionRol.usuario_id]"},
    )


class AsignacionRol(SQLModel, table=True):
    __tablename__ = "asignacion_rol"
    __table_args__ = (
        CheckConstraint(
            "rol IN ('ADMIN', 'VENDEDOR', 'CLIENTE')",
            name="rol_valido",
        ),
        Index(
            "uq_asignacion_rol_usuario_rol_vigente",
            "usuario_id",
            "rol",
            unique=True,
            postgresql_where=text("revocada_en IS NULL"),
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", index=True)
    rol: str = Field(max_length=50)
    desde: datetime = Field(sa_type=DateTime(timezone=True))
    vence_en: datetime | None = Field(default=None, sa_type=DateTime(timezone=True), nullable=True)
    revocada_en: datetime | None = Field(default=None, sa_type=DateTime(timezone=True), nullable=True)
    otorgada_por: int | None = Field(default=None, foreign_key="usuario.id", index=True, nullable=True)

    usuario: Optional[Usuario] = Relationship(
        back_populates="asignaciones",
        sa_relationship_kwargs={"foreign_keys": "[AsignacionRol.usuario_id]"},
    )
    otorgada_por_usuario: Optional[Usuario] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[AsignacionRol.otorgada_por]"},
    )


class IntentoAcceso(SQLModel, table=True):
    __tablename__ = "intento_acceso"
    __table_args__ = (
        Index(
            "ix_intento_acceso_email_ip_cuando",
            "email",
            "ip",
            "cuando",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    cuando: datetime = Field(sa_type=DateTime(timezone=True))
    email: str = Field(max_length=255)
    ip: str = Field(max_length=45)
    exito: bool = Field()


class EventoSeguridad(SQLModel, table=True):
    __tablename__ = "evento_seguridad"

    id: int | None = Field(default=None, primary_key=True)
    cuando: datetime = Field(sa_type=DateTime(timezone=True))
    actor: str = Field(max_length=100)
    accion: str = Field(max_length=255)
