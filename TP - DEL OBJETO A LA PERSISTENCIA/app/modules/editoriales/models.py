# Antes que SQLModel defina la tabla: fija la naming convention de constraints,
# así uq_<tabla>_<col> no depende del orden de imports.
import app.core.base  # noqa: F401
from sqlmodel import Field, SQLModel


class Editorial(SQLModel, table=True):
    __tablename__ = "editorial"

    id: int | None = Field(default=None, primary_key=True)
    # unique SIN index: así se crea la constraint uq_editorial_nombre (clave del 409).
    nombre: str = Field(max_length=150, unique=True)
    pais: str = Field(max_length=100)

    # TODO(fase 2b): libros: list["Libro"] = Relationship(back_populates="editorial")
