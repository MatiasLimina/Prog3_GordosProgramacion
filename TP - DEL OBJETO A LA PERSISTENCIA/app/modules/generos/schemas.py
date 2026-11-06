from pydantic import BaseModel, ConfigDict, Field


class GeneroCreate(BaseModel):
    # extra="forbid": un `id` (o cualquier campo no declarado) en el cuerpo es 422.
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(min_length=1, max_length=100)


class GeneroRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
