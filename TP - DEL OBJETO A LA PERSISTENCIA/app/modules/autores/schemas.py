from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


class AutorCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    nacionalidad: str = Field(min_length=1, max_length=100)

    @field_validator("nombre", "nacionalidad")
    @classmethod
    def no_vacio(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("No puede estar vacío.")
        return valor


class AutorUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    nacionalidad: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("nombre", "nacionalidad", mode="before")
    @classmethod
    def no_null(cls, valor):
        if valor is None:
            raise ValueError("No puede ser null; omití el campo para no modificarlo.")
        return valor


class AutorRead(BaseModel):
    id: int
    nombre: str
    nacionalidad: str


class AutorLibroRead(BaseModel):
    id: int
    isbn: str
    titulo: str
    precio: Decimal
    stock: int
    rol: str
    orden: int
