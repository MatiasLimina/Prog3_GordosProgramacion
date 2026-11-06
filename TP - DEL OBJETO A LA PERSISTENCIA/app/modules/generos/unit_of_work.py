"""UoW del módulo `generos`: compone los repositorios con la misma sesión.

`libros` es el repositorio de libros (del módulo `libros`) que usa el sub-listado
`/generos/{id}/libros`. `MENSAJES` elige el 409 por nombre de constraint.
"""
from collections.abc import Mapping
from typing import ClassVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.unit_of_work import UnitOfWork
from app.modules.generos.repository import GeneroRepository
from app.modules.libros.repository import LibroRepository


class GenerosUoW(UnitOfWork):
    MENSAJES: ClassVar[Mapping[str, str]] = {
        "uq_genero_nombre": "Ya existe un género con ese nombre.",
    }

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
        self.generos = GeneroRepository(session)
        self.libros = LibroRepository(session)
