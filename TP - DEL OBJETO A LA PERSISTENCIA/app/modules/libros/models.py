# Antes que SQLModel defina la tabla: fija la naming convention de constraints.
import app.core.base  # noqa: F401

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, DateTime, Index, Numeric, text
from sqlalchemy.sql import func
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.autores.models import Autor
    from app.modules.editoriales.models import Editorial
    from app.modules.generos.models import Genero
    from app.modules.usuarios.models import Usuario
    from app.modules.ventas.models import RenglonVenta, Venta


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
        # Índice único PARCIAL: el ISBN no puede repetirse entre libros vigentes, pero un
        # libro dado de baja (borrado_en no nulo) libera el ISBN. Lleva nombre propio para
        # entrar en MENSAJES (409) como cualquier UNIQUE.
        Index(
            "uq_libro_isbn_vigente",
            "isbn",
            unique=True,
            postgresql_where=text("borrado_en IS NULL"),
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    isbn: str = Field(max_length=30)
    titulo: str = Field(max_length=255)
    precio: Decimal = Field(sa_type=Numeric(10, 2))
    stock: int = Field(default=0)
    editorial_id: int = Field(foreign_key="editorial.id", index=True)
    genero_id: int | None = Field(default=None, foreign_key="genero.id", index=True, nullable=True)
    # Borrado lógico: None = vigente; con fecha = dado de baja (timestamptz).
    borrado_en: datetime | None = Field(default=None, sa_type=DateTime(timezone=True), nullable=True)

    editorial: Optional["Editorial"] = Relationship(back_populates="libros")
    genero: Optional["Genero"] = Relationship(back_populates="libros")
    autorias: list[LibroAutor] = Relationship(back_populates="libro", cascade_delete=True)
    renglones: list["RenglonVenta"] = Relationship(back_populates="libro")
    # Sin cascade_delete y con passive_deletes="all": movimiento_stock es de sólo agregado,
    # así que borrar un libro con movimientos debe fallar por FK, no poner nulos ni borrar.
    movimientos: list["MovimientoStock"] = Relationship(
        back_populates="libro", sa_relationship_kwargs={"passive_deletes": "all"}
    )


class MovimientoStock(SQLModel, table=True):
    """Movimiento de stock (sólo agregado; el disparador lo instala la 4ª migración)."""

    __tablename__ = "movimiento_stock"
    __table_args__ = (CheckConstraint("cantidad <> 0", name="cantidad_no_cero"),)

    id: int | None = Field(default=None, primary_key=True)
    libro_id: int = Field(foreign_key="libro.id", index=True)
    venta_id: int | None = Field(default=None, foreign_key="venta.id", index=True, nullable=True)
    # FK por texto: el módulo usuarios se referencia bajo TYPE_CHECKING (sin import circular).
    usuario_id: int = Field(foreign_key="usuario.id", index=True)
    # Signo = entrada (+) o salida (-); cero no tiene sentido.
    cantidad: int = Field()
    motivo: str = Field(max_length=255)
    # server_default: un solo reloj (la base), también para inserciones fuera del ORM.
    cuando: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now(), "nullable": False},
    )

    libro: Optional["Libro"] = Relationship(back_populates="movimientos")
    venta: Optional["Venta"] = Relationship(back_populates="movimientos")
    usuario: Optional["Usuario"] = Relationship(back_populates="movimientos")
