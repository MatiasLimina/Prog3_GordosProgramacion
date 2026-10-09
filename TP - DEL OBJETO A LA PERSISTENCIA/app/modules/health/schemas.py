from pydantic import BaseModel


class LiveRead(BaseModel):
    estado: str


class ReadyRead(BaseModel):
    estado: str
    base_de_datos: str
