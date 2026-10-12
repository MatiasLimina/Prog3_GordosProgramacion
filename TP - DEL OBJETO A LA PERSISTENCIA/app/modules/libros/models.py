# Antes que SQLModel defina la tabla: fija la naming convention de constraints.
import app.core.base  # noqa: F401

from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Numeric
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.autores.models import Autor
    from app.modules.editoriales.models import Editorial
    from app.modules.generos.models import Genero


class LibroAutor(SQLModel, table=True):
    __tablename__ = "libro_autor"
    __table_args__ = (
        CheckConstraint("orden >= 1", name="orden_positivo"),
        CheckConstraint(
            "rol IN ('autor', 'coautor', 'traductor', 'ilustrador')",
            name="rol_valido",
        ),
    )

    libro_id: int = Field(foreign_key="libro.id", primary_key=True, index=True)
    autor_id: int = Field(foreign_key="autor.id", primary_key=True, index=True)
    rol: str = Field(max_length=50)
    orden: int = Field()

    libro: Optional["Libro"] = Relationship(back_populates="autorias")
    autor: Optional["Autor"] = Relationship(back_populates="autorias")


class Libro(SQLModel, table=True):
    __tablename__ = "libro"
    __table_args__ = (
        CheckConstraint("precio > 0", name="precio_positivo"),
        CheckConstraint("stock >= 0", name="stock_no_negativo"),
    )

    id: int | None = Field(default=None, primary_key=True)
    isbn: str = Field(max_length=30, unique=True)
    titulo: str = Field(max_length=255)
    precio: Decimal = Field(sa_type=Numeric(10, 2))
    stock: int = Field(default=0)
    editorial_id: int = Field(foreign_key="editorial.id", index=True)
    genero_id: int | None = Field(default=None, foreign_key="genero.id", index=True, nullable=True)

    editorial: Optional["Editorial"] = Relationship(back_populates="libros")
    genero: Optional["Genero"] = Relationship(back_populates="libros")
    autorias: list[LibroAutor] = Relationship(back_populates="libro", cascade_delete=True)
    # TODO(integrante C): restaurar cuando exista app.modules.ventas.models.RenglonVenta
    # (agregar tambien "from app.modules.ventas.models import RenglonVenta" bajo TYPE_CHECKING):
    #     renglones: list["RenglonVenta"] = Relationship(back_populates="libro")
    # Se quito temporalmente porque RenglonVenta aun no existe y el mapper no resuelve el string.
