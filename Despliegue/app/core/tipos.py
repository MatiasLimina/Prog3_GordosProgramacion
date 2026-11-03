"""Tipos compartidos para enteros que van a columnas INTEGER (int32) de PostgreSQL.

Sin límite superior, un id o stock gigante llega a la base y revienta con
"value out of int32 range" (500). Con estos tipos responde 422.
"""
from typing import Annotated

from fastapi import Path
from pydantic import Field

INT32_MAX = 2_147_483_647

# En DTO (cuerpos JSON): ids >= 1 y dentro de int32.
IdDto = Annotated[int, Field(ge=1, le=INT32_MAX)]
# Stock: >= 0 y dentro de int32.
StockDto = Annotated[int, Field(ge=0, le=INT32_MAX)]

# En parámetros de ruta ({id}). Para filtros de query: Query(ge=1, le=INT32_MAX).
IdPath = Annotated[int, Path(ge=1, le=INT32_MAX)]
