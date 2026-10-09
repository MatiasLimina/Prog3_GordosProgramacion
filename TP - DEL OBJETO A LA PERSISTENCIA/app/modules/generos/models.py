from sqlmodel import Field, SQLModel


class Genero(SQLModel, table=True):
    __tablename__ = "genero"

    id: int | None = Field(default=None, primary_key=True)
    # unique SIN index: así se crea la constraint uq_genero_nombre (clave del 409).
    nombre: str = Field(max_length=100, unique=True)

    # TODO(fase 2b): libros: list["Libro"] = Relationship(back_populates="genero")
