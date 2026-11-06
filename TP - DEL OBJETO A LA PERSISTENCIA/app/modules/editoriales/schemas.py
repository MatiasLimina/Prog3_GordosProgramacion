from pydantic import BaseModel, ConfigDict, Field, field_validator


class EditorialCreate(BaseModel):
    # extra="forbid": un `id` (o cualquier campo no declarado) en el cuerpo es 422.
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(min_length=1, max_length=150)
    pais: str = Field(min_length=1, max_length=100)


class EditorialUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    pais: str | None = Field(default=None, min_length=1, max_length=100)

    # Los campos se pueden OMITIR, pero no enviar null: las columnas son NOT NULL.
    # Un validador no corre sobre los defaults, así que omitir sigue siendo válido
    # y exclude_unset no ve el campo.
    @field_validator("nombre", "pais", mode="before")
    @classmethod
    def no_null(cls, valor):
        if valor is None:
            raise ValueError("No puede ser null; omití el campo para no modificarlo.")
        return valor


class EditorialRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    pais: str
