from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator



def _no_vacio(valor: str) -> str:
    if not valor.strip():
        raise ValueError("No puede estar vacío.")
    return valor


class ClienteCreate(BaseModel):
    # extra="forbid": un `id` (u otro campo desconocido) en el cuerpo es un 422 claro.
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(min_length=1, max_length=150)
    # EmailStr (email-validator viene con fastapi[standard]); max 255 = columna.
    email: EmailStr = Field(max_length=255)

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, valor: str) -> str:
        return _no_vacio(valor)


class ClienteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    email: EmailStr | None = Field(default=None, max_length=255)

    @field_validator("nombre", "email", mode="before")
    @classmethod
    def no_null(cls, valor):
        if valor is None:
            raise ValueError("No puede ser null; omití el campo para no modificarlo.")
        return valor

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, valor: str) -> str:
        return _no_vacio(valor)


class ClienteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: str


class PerfilCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    telefono: str = Field(min_length=1, max_length=50)
    direccion: str = Field(min_length=1, max_length=255)

    @field_validator("telefono", "direccion")
    @classmethod
    def no_vacio(cls, valor: str) -> str:
        return _no_vacio(valor)


class PerfilRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cliente_id: int
    telefono: str
    direccion: str


class ClienteDetalleRead(ClienteRead):
    """Cliente con su perfil (None si todavía no tiene)."""

    perfil: PerfilRead | None = None
