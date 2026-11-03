from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.tipos import INT32_MAX, IdDto


# Entrada. Precio unitario, subtotal, total y fecha los calcula el servidor
# (RN-06, RN-07): extra="forbid" hace que enviarlos sea un 422 explícito en
# vez de ignorarlos en silencio.
class RenglonCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    libro_id: IdDto
    cantidad: int = Field(ge=1, le=INT32_MAX)


class VentaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cliente_id: IdDto
    renglones: list[RenglonCreate] = Field(min_length=1)  # RN-05: al menos un renglón

    @field_validator("renglones")
    @classmethod
    def sin_libros_repetidos(cls, renglones: list[RenglonCreate]) -> list[RenglonCreate]:
        ids = [r.libro_id for r in renglones]
        if len(ids) != len(set(ids)):
            raise ValueError("No se puede repetir un libro en los renglones de una venta.")
        return renglones


# Salida.
class ClienteSimpleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: str


class RenglonRead(BaseModel):
    libro_id: int
    titulo: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class VentaRead(BaseModel):
    id: int
    fecha: datetime
    total: Decimal
    cliente: ClienteSimpleRead
    renglones: list[RenglonRead]
