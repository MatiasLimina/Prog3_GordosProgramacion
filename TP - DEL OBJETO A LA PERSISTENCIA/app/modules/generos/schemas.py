from pydantic import BaseModel, Field


class GeneroCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)


class GeneroRead(BaseModel):
    id: int
    nombre: str
