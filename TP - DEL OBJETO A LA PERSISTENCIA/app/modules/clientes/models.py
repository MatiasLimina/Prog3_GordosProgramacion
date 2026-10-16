# Antes que SQLModel defina la tabla: fija la naming convention de constraints.
import app.core.base  # noqa: F401

from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.ventas.models import Venta


class Cliente(SQLModel, table=True):
    __tablename__ = "cliente"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=150)
    # unique SIN index: así se crea la constraint uq_cliente_email (clave del 409).
    email: str = Field(max_length=255, unique=True)

    perfil: Optional["PerfilCliente"] = Relationship(
        back_populates="cliente", sa_relationship_kwargs={"uselist": False}
    )
    ventas: list["Venta"] = Relationship(back_populates="cliente")


class PerfilCliente(SQLModel, table=True):
    __tablename__ = "perfil_cliente"

    id: int | None = Field(default=None, primary_key=True)
    # unique SIN index: el UNIQUE (1:1) ya crea su índice -> uq_perfil_cliente_cliente_id.
    cliente_id: int = Field(foreign_key="cliente.id", unique=True)
    telefono: str = Field(max_length=50)
    direccion: str = Field(max_length=255)

    cliente: Optional["Cliente"] = Relationship(back_populates="perfil")
