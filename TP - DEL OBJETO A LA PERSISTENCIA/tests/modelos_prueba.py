"""Modelos sólo de test, fuera de `SQLModel.metadata`.

Tienen su propio `registry()`: así el `TRUNCATE` de `tests/conftest.py` y el autogenerate
de Alembic no ven sus tablas. Cada test que las necesita las crea y las borra con SQL
explícito (nunca `create_all`; el esquema real sólo se crea con Alembic).
"""
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import registry
from sqlmodel import Field, Relationship, SQLModel


class _BasePrueba(SQLModel, registry=registry()):
    pass


class Borrable(_BasePrueba, table=True):
    """Imita a `Libro` de CHG-07: `borrado_en` timestamptz nullable."""

    __tablename__ = "prueba_borrable"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=50)
    borrado_en: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))


# DDL explícito de la tabla de prueba (ver fixture `tabla_borrable` en test_repository_db.py).
CREAR_TABLA_BORRABLE = """
CREATE TABLE prueba_borrable (
    id serial PRIMARY KEY,
    nombre varchar(50) NOT NULL,
    borrado_en timestamptz NULL
)
"""


class Padre(_BasePrueba, table=True):
    """Padre de una colección, para probar la precarga sin depender de las tablas reales."""

    __tablename__ = "prueba_padre"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=50)
    hijos: list["Hijo"] = Relationship(back_populates="padre")


class Hijo(_BasePrueba, table=True):
    __tablename__ = "prueba_hijo"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=50)
    padre_id: int = Field(foreign_key="prueba_padre.id")
    padre: Padre | None = Relationship(back_populates="hijos")


# DDL explícito (ver fixture `tablas_padre_hijo` en test_repository_db.py); se borran en orden inverso.
CREAR_TABLAS_PADRE_HIJO = (
    "CREATE TABLE prueba_padre (id serial PRIMARY KEY, nombre varchar(50) NOT NULL)",
    """CREATE TABLE prueba_hijo (
    id serial PRIMARY KEY,
    nombre varchar(50) NOT NULL,
    padre_id integer NOT NULL REFERENCES prueba_padre (id)
)""",
)
BORRAR_TABLAS_PADRE_HIJO = ("DROP TABLE IF EXISTS prueba_hijo", "DROP TABLE IF EXISTS prueba_padre")
